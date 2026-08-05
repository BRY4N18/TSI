"""Informes tácticos simples del módulo Seguimiento y Cierre de Casos (Pinot, solo lectura).

Ver specs/002-tactico/Emergencias/informes-tacticos-simples/backend/data-model.md.
"""

from __future__ import annotations

from typing import Any

from core.pinot.client import PinotClient
from core.repositories.accidentes.estado_accidente_repository import ESTADO_IDS
from core.repositories.informes_tacticos._catalogo_utils import unidades_by_id
from core.repositories.informes_tacticos._periodo_utils import periodo_str

ASIGNADO_ID = ESTADO_IDS["ASIGNADO"]
CERRADO_ID = ESTADO_IDS["CERRADO"]


class SeguimientoRepository:
    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def tiempo_asignado_cerrado(self, desde_ms: int, hasta_ms: int) -> list[dict[str, Any]]:
        """Informe 1/3: tiempo promedio entre 'asignado' y 'cerrado', por unidad.

        MVP: agrupa por unidad (la que atendió el despacho del accidente); el
        corte por zona geográfica queda diferido, mismo criterio que los
        informes de Registro (ver `registro_repository.py`).
        """
        sql = """
            SELECT idaccidente, idtipoestadoincidente, fechahoramodificado
            FROM Fact_AccidenteTipoEstadoAccidente
            WHERE fechahoramodificado >= %(desde)s AND fechahoramodificado <= %(hasta)s
                  AND idtipoestadoincidente IN (%(asignado)s, %(cerrado)s)
        """
        rows = self.pinot.query(sql, {"desde": desde_ms, "hasta": hasta_ms, "asignado": ASIGNADO_ID, "cerrado": CERRADO_ID})
        por_accidente: dict[str, dict[int, int]] = {}
        for r in rows:
            por_accidente.setdefault(r["idaccidente"], {})[r["idtipoestadoincidente"]] = r[
                "fechahoramodificado"
            ]
        pares = {
            aid: v[CERRADO_ID] - v[ASIGNADO_ID]
            for aid, v in por_accidente.items()
            if ASIGNADO_ID in v and CERRADO_ID in v
        }
        if not pares:
            return []

        despachos_sql = "SELECT idaccidente, idunidademergencia FROM Fact_Despacho WHERE idaccidente IN %(ids)s"
        despachos = self.pinot.query(despachos_sql, {"ids": list(pares.keys())})
        unidad_por_accidente = {d["idaccidente"]: d["idunidademergencia"] for d in despachos}

        tiempos_por_unidad: dict[int, list[int]] = {}
        for aid, diff in pares.items():
            unidad = unidad_por_accidente.get(aid)
            if unidad is None:
                continue
            tiempos_por_unidad.setdefault(unidad, []).append(diff)

        nombres = unidades_by_id(self.pinot, list(tiempos_por_unidad.keys()))
        return [
            {
                "idunidademergencia": k,
                "unidad_nombre": nombres.get(k, {}).get("nombre"),
                "unidad_placa": nombres.get(k, {}).get("placa"),
                "promedio_segundos": round((sum(v) / len(v)) / 1000, 2),
            }
            for k, v in sorted(tiempos_por_unidad.items())
        ]

    def cierres_forzados(self, desde_ms: int, hasta_ms: int, datetrunc_unit: str) -> list[dict[str, Any]]:
        """Informe 2/3: % de cierres forzados sobre total de cierres, por período.

        "Forzado" = transición a `Retirado` con `idusuario` poblado (retiro manual
        desde central vía `ForzarRetiroService`/`RetiroDespachoService`, ver
        `auditoria-esquemas-informes-v2.md` líneas 68-73); un retiro automático
        por vencimiento no lleva `idusuario`. Campo añadido al esquema el
        2026-08-02 (ver `.specify/docs/changelog.md`) — antes de eso no existía
        forma de distinguirlo y se aproximaba con `estadonuevo == 'Retirado'` solo.
        """
        sql = f"""
            SELECT DATETRUNC('{datetrunc_unit}', fechahora, 'MILLISECONDS') AS periodo, estadonuevo, idusuario
            FROM Fact_HistorialDespachoUnidad
            WHERE fechahora >= %(desde)s AND fechahora <= %(hasta)s
                  AND estadonuevo IN ('Retirado', 'Cerrado')
        """
        rows = self.pinot.query(sql, {"desde": desde_ms, "hasta": hasta_ms})
        totales: dict[str, int] = {}
        forzados: dict[str, int] = {}
        for r in rows:
            periodo = periodo_str(r["periodo"])
            totales[periodo] = totales.get(periodo, 0) + 1
            if r["estadonuevo"] == "Retirado" and r.get("idusuario") is not None:
                forzados[periodo] = forzados.get(periodo, 0) + 1
        return [
            {"periodo": k, "pct_cierres_forzados": round(forzados.get(k, 0) / v, 4) if v else 0.0}
            for k, v in sorted(totales.items())
        ]

    def abortos_perdidas(self, desde_ms: int, hasta_ms: int) -> list[dict[str, Any]]:
        """Informe 3/3: % de abortos/pérdidas sobre total de despachos, por unidad."""
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
        abortos: dict[int, int] = {}
        for h in historial:
            unidad = unidad_por_despacho.get(h["iddespacho"])
            if unidad is None:
                continue
            totales[unidad] = totales.get(unidad, 0) + 1
            if h["estadonuevo"] == "Abortado":
                abortos[unidad] = abortos.get(unidad, 0) + 1

        nombres = unidades_by_id(self.pinot, list(totales.keys()))
        return [
            {
                "idunidademergencia": unidad,
                "unidad_nombre": nombres.get(unidad, {}).get("nombre"),
                "unidad_placa": nombres.get(unidad, {}).get("placa"),
                "pct_abortos_perdidas": round(abortos.get(unidad, 0) / total, 4) if total else 0.0,
            }
            for unidad, total in sorted(totales.items())
        ]
