"""Informes tácticos simples del módulo Despacho Inteligente (Pinot, solo lectura).

Ver specs/002-tactico/Emergencias/informes-tacticos-simples/backend/data-model.md.
Pinot no soporta JOIN entre tablas: los cruces (unidad->condado, calle->condado,
despacho->severidad del accidente) se resuelven con una segunda consulta acotada
por el mismo rango de fechas y un merge en Python — mismo patrón que el resto
del proyecto usa para resolver relaciones entre tablas Pinot.
"""

from __future__ import annotations

from typing import Any

from core.pinot.client import PinotClient
from core.repositories.accidentes.estado_accidente_repository import ESTADO_IDS
from core.repositories.informes_tacticos._catalogo_utils import (
    condados_by_id,
    origenes_despacho,
    unidades_by_id,
)

REPORTADO_ID = ESTADO_IDS["REPORTADO"]
ASIGNADO_ID = ESTADO_IDS["ASIGNADO"]
RECHAZO_TIMEOUT_ESTADOS = ("Rechazado", "Timeout")


class DespachoRepository:
    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def _unidades_by_condado(self, idcondado: int) -> set[int]:
        rows = self.pinot.query(
            "SELECT idunidademergencia FROM Dim_UnidadEmergencia WHERE idcondado IN %(idscondado)s",
            {"idscondado": [idcondado]},
        )
        return {r["idunidademergencia"] for r in rows}

    def asignacion_automatica_vs_manual(
        self, desde_ms: int, hasta_ms: int, idcondado: int | None = None
    ) -> list[dict[str, Any]]:
        """Informe 1/6: % de asignaciones automáticas vs. manuales/escaladas."""
        sql = """
            SELECT idorigendespacho, idunidademergencia
            FROM Fact_Despacho
            WHERE fechahoradespacho >= %(desde)s AND fechahoradespacho <= %(hasta)s
        """
        rows = self.pinot.query(sql, {"desde": desde_ms, "hasta": hasta_ms})
        if idcondado is not None:
            unidades = self._unidades_by_condado(idcondado)
            rows = [r for r in rows if r.get("idunidademergencia") in unidades]

        total = len(rows)
        buckets: dict[int, int] = {}
        for r in rows:
            buckets[r["idorigendespacho"]] = buckets.get(r["idorigendespacho"], 0) + 1
        nombres = origenes_despacho(self.pinot)
        return [
            {
                "idorigendespacho": k,
                "origen_nombre": nombres.get(k),
                "pct_total": round(v / total, 4) if total else 0.0,
            }
            for k, v in sorted(buckets.items())
        ]

    def tiempo_reportado_confirmado(self, desde_ms: int, hasta_ms: int) -> dict[str, Any]:
        """Informe 2/6: tiempo promedio entre 'reportado' y 'confirmado' (ASIGNADO)."""
        sql = """
            SELECT idaccidente, idtipoestadoincidente, fechahoramodificado
            FROM Fact_AccidenteTipoEstadoAccidente
            WHERE fechahoramodificado >= %(desde)s AND fechahoramodificado <= %(hasta)s
                  AND idtipoestadoincidente IN (%(reportado)s, %(asignado)s)
        """
        rows = self.pinot.query(
            sql, {"desde": desde_ms, "hasta": hasta_ms, "reportado": REPORTADO_ID, "asignado": ASIGNADO_ID}
        )
        por_accidente: dict[str, dict[int, int]] = {}
        for r in rows:
            por_accidente.setdefault(r["idaccidente"], {})[r["idtipoestadoincidente"]] = r[
                "fechahoramodificado"
            ]

        diffs = [
            v[ASIGNADO_ID] - v[REPORTADO_ID]
            for v in por_accidente.values()
            if REPORTADO_ID in v and ASIGNADO_ID in v
        ]
        promedio_ms = sum(diffs) / len(diffs) if diffs else 0.0
        return {"promedio_segundos": round(promedio_ms / 1000, 2)}

    def tiempo_respuesta_por_severidad(
        self, desde_ms: int, hasta_ms: int, idcondado: int | None = None
    ) -> list[dict[str, Any]]:
        """Informe 3/6: distribución del tiempo de respuesta por severidad."""
        # `fechahorallegada IS NOT NULL` en Pinot no filtra el sentinel de "sin valor"
        # (enableColumnBasedNullHandling=false, ver docstring de PinotClient) — se
        # filtra en Python después de que el cliente coerciona el sentinel a None.
        despachos_sql = """
            SELECT idaccidente, idunidademergencia, fechahoradespacho, fechahorallegada
            FROM Fact_Despacho
            WHERE fechahoradespacho >= %(desde)s AND fechahoradespacho <= %(hasta)s
        """
        despachos = self.pinot.query(despachos_sql, {"desde": desde_ms, "hasta": hasta_ms})
        despachos = [d for d in despachos if d.get("fechahorallegada") is not None]
        if idcondado is not None:
            unidades = self._unidades_by_condado(idcondado)
            despachos = [d for d in despachos if d.get("idunidademergencia") in unidades]
        if not despachos:
            return []

        idaccidentes = list({d["idaccidente"] for d in despachos})
        accidentes_sql = "SELECT idaccidente, idseveridad FROM Fact_Accidente WHERE idaccidente IN %(ids)s"
        accidentes = self.pinot.query(accidentes_sql, {"ids": idaccidentes})
        severidad_por_accidente = {a["idaccidente"]: a["idseveridad"] for a in accidentes}

        tiempos_por_severidad: dict[int, list[int]] = {}
        for d in despachos:
            severidad = severidad_por_accidente.get(d["idaccidente"])
            if severidad is None:
                continue
            tiempo = d["fechahorallegada"] - d["fechahoradespacho"]
            tiempos_por_severidad.setdefault(severidad, []).append(tiempo)

        return [
            {"idseveridad": k, "promedio_segundos": round((sum(v) / len(v)) / 1000, 2)}
            for k, v in sorted(tiempos_por_severidad.items())
        ]

    def rechazo_timeout_por_unidad(self, desde_ms: int, hasta_ms: int) -> list[dict[str, Any]]:
        """Informe 4/6: % de rechazo/timeout por unidad."""
        historial_sql = """
            SELECT iddespacho, estadonuevo
            FROM Fact_HistorialDespachoUnidad
            WHERE fechahora >= %(desde)s AND fechahora <= %(hasta)s
        """
        historial = self.pinot.query(historial_sql, {"desde": desde_ms, "hasta": hasta_ms})
        if not historial:
            return []

        iddespachos = list({h["iddespacho"] for h in historial})
        despachos_sql = "SELECT iddespacho, idunidademergencia FROM Fact_Despacho WHERE iddespacho IN %(ids)s"
        despachos = self.pinot.query(despachos_sql, {"ids": iddespachos})
        unidad_por_despacho = {d["iddespacho"]: d["idunidademergencia"] for d in despachos}

        totales: dict[int, int] = {}
        rechazos: dict[int, int] = {}
        for h in historial:
            unidad = unidad_por_despacho.get(h["iddespacho"])
            if unidad is None:
                continue
            totales[unidad] = totales.get(unidad, 0) + 1
            if h["estadonuevo"] in RECHAZO_TIMEOUT_ESTADOS:
                rechazos[unidad] = rechazos.get(unidad, 0) + 1

        nombres = unidades_by_id(self.pinot, list(totales.keys()))
        return [
            {
                "idunidademergencia": unidad,
                "unidad_nombre": nombres.get(unidad, {}).get("nombre"),
                "unidad_placa": nombres.get(unidad, {}).get("placa"),
                "pct_rechazo_timeout": round(rechazos.get(unidad, 0) / total, 4) if total else 0.0,
            }
            for unidad, total in sorted(totales.items())
        ]

    def carga_por_unidad(self, desde_ms: int, hasta_ms: int) -> list[dict[str, Any]]:
        """Informe 5/6: carga de despachos atendidos por unidad."""
        sql = """
            SELECT idunidademergencia, COUNT(*) AS total_despachos
            FROM Fact_Despacho
            WHERE fechahoradespacho >= %(desde)s AND fechahoradespacho <= %(hasta)s
            GROUP BY idunidademergencia
            ORDER BY idunidademergencia
        """
        rows = self.pinot.query(sql, {"desde": desde_ms, "hasta": hasta_ms})
        nombres = unidades_by_id(self.pinot, [r["idunidademergencia"] for r in rows])
        for r in rows:
            info = nombres.get(r["idunidademergencia"], {})
            r["unidad_nombre"] = info.get("nombre")
            r["unidad_placa"] = info.get("placa")
        return rows

    def ratio_demanda_capacidad(self, desde_ms: int, hasta_ms: int) -> list[dict[str, Any]]:
        """Informe 6/6: ratio demanda/capacidad por condado.

        Resuelve `Fact_Accidente.idcalle -> Dim_Calle.idciudad -> Dim_Ciudad.idcondado`
        para agrupar la demanda al mismo nivel geográfico (condado) que la
        capacidad (`Dim_UnidadEmergencia.idcondado`, activas).
        """
        accidentes_sql = """
            SELECT idcalle FROM Fact_Accidente
            WHERE fechahoraaccidente >= %(desde)s AND fechahoraaccidente <= %(hasta)s
        """
        accidentes = self.pinot.query(accidentes_sql, {"desde": desde_ms, "hasta": hasta_ms})
        if not accidentes:
            return []

        idcalles = list({a["idcalle"] for a in accidentes if a.get("idcalle") is not None})
        calles = self.pinot.query(
            "SELECT idcalle, idciudad FROM Dim_Calle WHERE idcalle IN %(ids)s", {"ids": idcalles}
        )
        idciudades = list({c["idciudad"] for c in calles})
        ciudades = self.pinot.query(
            "SELECT idciudad, idcondado FROM Dim_Ciudad WHERE idciudad IN %(ids)s", {"ids": idciudades}
        )
        condado_por_ciudad = {c["idciudad"]: c["idcondado"] for c in ciudades}
        condado_por_calle = {
            c["idcalle"]: condado_por_ciudad.get(c["idciudad"]) for c in calles
        }

        accidentes_por_condado: dict[int, int] = {}
        for a in accidentes:
            condado = condado_por_calle.get(a.get("idcalle"))
            if condado is None:
                continue
            accidentes_por_condado[condado] = accidentes_por_condado.get(condado, 0) + 1

        unidades_activas = self.pinot.query(
            "SELECT idcondado FROM Dim_UnidadEmergencia WHERE activo = true", {}
        )
        unidades_por_condado: dict[int, int] = {}
        for u in unidades_activas:
            unidades_por_condado[u["idcondado"]] = unidades_por_condado.get(u["idcondado"], 0) + 1

        condados = set(accidentes_por_condado) | set(unidades_por_condado)
        nombres = condados_by_id(self.pinot, list(condados))
        resultado = []
        for condado in sorted(condados):
            total_accidentes = accidentes_por_condado.get(condado, 0)
            unidades = unidades_por_condado.get(condado, 0)
            resultado.append(
                {
                    "idcondado": condado,
                    "condado_nombre": nombres.get(condado),
                    "total_accidentes": total_accidentes,
                    "unidades_activas": unidades,
                    "ratio": round(total_accidentes / unidades, 4) if unidades else None,
                }
            )
        return resultado
