"""Informes tácticos simples del módulo Registro de Accidente — Fact_Accidente (Pinot, solo lectura).

Ver specs/002-tactico/Emergencias/informes-tacticos-simples/backend/data-model.md
para la fórmula de agregación de cada informe.
"""

from __future__ import annotations

from typing import Any

from core.pinot.client import PinotClient
from core.repositories.accidentes.estado_accidente_repository import ESTADO_IDS
from core.repositories.informes_tacticos._periodo_utils import periodo_str

DESCARTADO_ID = ESTADO_IDS["DESCARTADO"]
FUSIONADO_ID = ESTADO_IDS["FUSIONADO"]


class RegistroRepository:
    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def _nombres_calles(self, idcalles: list[int]) -> dict[int, str]:
        """Resuelve idcalle -> nombre real (Dim_Calle) para las 3 informes agrupados por calle.

        Pinot no soporta JOIN: segunda consulta acotada por los ids ya
        agregados, igual que `despacho_repository._unidades_by_condado`.
        """
        if not idcalles:
            return {}
        rows = self.pinot.query(
            "SELECT idcalle, calle FROM Dim_Calle WHERE idcalle IN %(ids)s",
            {"ids": idcalles},
        )
        return {r["idcalle"]: r.get("calle") for r in rows}

    def volumen_casos(self, desde_ms: int, hasta_ms: int, datetrunc_unit: str) -> list[dict[str, Any]]:
        """Volumen total de casos registrados, por período (informe 1/7 de Registro)."""
        sql = f"""
            SELECT DATETRUNC('{datetrunc_unit}', fechahoraaccidente, 'MILLISECONDS') AS periodo,
                   COUNT(*) AS total_casos
            FROM Fact_Accidente
            WHERE fechahoraaccidente >= %(desde)s AND fechahoraaccidente <= %(hasta)s
            GROUP BY periodo
            ORDER BY periodo
        """
        rows = self.pinot.query(sql, {"desde": desde_ms, "hasta": hasta_ms})
        for row in rows:
            row["periodo"] = periodo_str(row["periodo"])
        return rows

    def distribucion_severidad(self, desde_ms: int, hasta_ms: int) -> list[dict[str, Any]]:
        """Distribución de casos por nivel de severidad, por período (informe 2/7)."""
        sql = """
            SELECT idseveridad, COUNT(*) AS total_casos
            FROM Fact_Accidente
            WHERE fechahoraaccidente >= %(desde)s AND fechahoraaccidente <= %(hasta)s
            GROUP BY idseveridad
            ORDER BY idseveridad
        """
        return self.pinot.query(sql, {"desde": desde_ms, "hasta": hasta_ms})

    def distribucion_zona(self, desde_ms: int, hasta_ms: int) -> list[dict[str, Any]]:
        """Distribución de casos por zona, por período (informe 3/7).

        MVP: agrupa por `idcalle` (nivel geográfico disponible directamente en
        `Fact_Accidente`). Agrupar por ciudad/condado/estado requiere resolver
        la cadena `Dim_Calle -> Dim_Ciudad -> Dim_Condado -> Dim_Estado`, fuera
        de alcance de este primer corte — ver Assumptions de la spec.
        """
        sql = """
            SELECT idcalle, COUNT(*) AS total_casos
            FROM Fact_Accidente
            WHERE fechahoraaccidente >= %(desde)s AND fechahoraaccidente <= %(hasta)s
            GROUP BY idcalle
            ORDER BY idcalle
        """
        rows = self.pinot.query(sql, {"desde": desde_ms, "hasta": hasta_ms})
        nombres = self._nombres_calles([r["idcalle"] for r in rows])
        for row in rows:
            row["calle_nombre"] = nombres.get(row["idcalle"])
        return rows

    def completitud_campos_criticos(
        self, desde_ms: int, hasta_ms: int, datetrunc_unit: str
    ) -> list[dict[str, Any]]:
        """% de registros con campos críticos completos, por período (informe 4/7)."""
        sql = f"""
            SELECT DATETRUNC('{datetrunc_unit}', fechahoraaccidente, 'MILLISECONDS') AS periodo,
                   COUNT(*) AS total_casos,
                   SUM(CASE WHEN idseveridad IS NOT NULL AND idcalle IS NOT NULL THEN 1 ELSE 0 END) AS total_completos
            FROM Fact_Accidente
            WHERE fechahoraaccidente >= %(desde)s AND fechahoraaccidente <= %(hasta)s
            GROUP BY periodo
            ORDER BY periodo
        """
        rows = self.pinot.query(sql, {"desde": desde_ms, "hasta": hasta_ms})
        for row in rows:
            row["periodo"] = periodo_str(row["periodo"])
            total = row.pop("total_casos", 0) or 0
            completos = row.pop("total_completos", 0) or 0
            row["pct_completos"] = round(completos / total, 4) if total else 0.0
        return rows

    def descarte_fusion(self, desde_ms: int, hasta_ms: int, datetrunc_unit: str) -> list[dict[str, Any]]:
        """% de descarte y de fusión sobre total de reportes, por período (informe 5/7)."""
        total_sql = f"""
            SELECT DATETRUNC('{datetrunc_unit}', fechahoraaccidente, 'MILLISECONDS') AS periodo,
                   COUNT(*) AS total_casos
            FROM Fact_Accidente
            WHERE fechahoraaccidente >= %(desde)s AND fechahoraaccidente <= %(hasta)s
            GROUP BY periodo
            ORDER BY periodo
        """
        estados_sql = f"""
            SELECT DATETRUNC('{datetrunc_unit}', fechahoramodificado, 'MILLISECONDS') AS periodo,
                   idtipoestadoincidente,
                   COUNT(*) AS total
            FROM Fact_AccidenteTipoEstadoAccidente
            WHERE fechahoramodificado >= %(desde)s AND fechahoramodificado <= %(hasta)s
                  AND idtipoestadoincidente IN (%(descartado)s, %(fusionado)s)
            GROUP BY periodo, idtipoestadoincidente
        """
        totales = self.pinot.query(sql=total_sql, params={"desde": desde_ms, "hasta": hasta_ms})
        estados = self.pinot.query(
            sql=estados_sql,
            params={
                "desde": desde_ms,
                "hasta": hasta_ms,
                "descartado": DESCARTADO_ID,
                "fusionado": FUSIONADO_ID,
            },
        )
        descartes_por_periodo: dict[str, int] = {}
        fusiones_por_periodo: dict[str, int] = {}
        for row in estados:
            periodo = periodo_str(row["periodo"])
            if int(row["idtipoestadoincidente"]) == DESCARTADO_ID:
                descartes_por_periodo[periodo] = row["total"]
            elif int(row["idtipoestadoincidente"]) == FUSIONADO_ID:
                fusiones_por_periodo[periodo] = row["total"]

        resultado = []
        for row in totales:
            periodo = periodo_str(row["periodo"])
            total = row["total_casos"] or 0
            descartes = descartes_por_periodo.get(periodo, 0)
            fusiones = fusiones_por_periodo.get(periodo, 0)
            resultado.append(
                {
                    "periodo": periodo,
                    "pct_descarte": round(descartes / total, 4) if total else 0.0,
                    "pct_fusion": round(fusiones / total, 4) if total else 0.0,
                }
            )
        return resultado

    def ranking_ubicaciones(self, desde_ms: int, hasta_ms: int, top: int) -> list[dict[str, Any]]:
        """Ranking de ubicaciones con mayor frecuencia de casos, por período (informe 6/7)."""
        sql = f"""
            SELECT idcalle, COUNT(*) AS total_casos
            FROM Fact_Accidente
            WHERE fechahoraaccidente >= %(desde)s AND fechahoraaccidente <= %(hasta)s
            GROUP BY idcalle
            ORDER BY total_casos DESC
            LIMIT {int(top)}
        """
        rows = self.pinot.query(sql, {"desde": desde_ms, "hasta": hasta_ms})
        nombres = self._nombres_calles([r["idcalle"] for r in rows])
        for row in rows:
            row["calle_nombre"] = nombres.get(row["idcalle"])
        return rows

    def impacto_humano(self, desde_ms: int, hasta_ms: int) -> list[dict[str, Any]]:
        """Impacto humano (víctimas, heridos, fallecidos) por región y período (informe 7/7).

        MVP: agrupa por `idcalle` como región (ver nota de `distribucion_zona`).
        """
        sql = """
            SELECT idcalle,
                   SUM(numvictimas) AS total_victimas,
                   SUM(numheridos) AS total_heridos,
                   SUM(numfallecidos) AS total_fallecidos
            FROM Fact_Accidente
            WHERE fechahoraaccidente >= %(desde)s AND fechahoraaccidente <= %(hasta)s
            GROUP BY idcalle
            ORDER BY idcalle
        """
        rows = self.pinot.query(sql, {"desde": desde_ms, "hasta": hasta_ms})
        nombres = self._nombres_calles([r["idcalle"] for r in rows])
        for row in rows:
            row["calle_nombre"] = nombres.get(row["idcalle"])
        return rows
