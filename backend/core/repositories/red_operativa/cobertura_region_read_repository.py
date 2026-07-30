"""Cobertura geográfica región ↔ unidades activas (CU-O62 / RN-REGON-005).

Regla confirmada: puente Dim_RegionOperativaEstadoRegion.idestadoregion →
Dim_Condado (idestadoregion|idestado) → Dim_UnidadEmergencia.idcondado (activo).
"""

from __future__ import annotations

from core.pinot.client import PinotClient


class CoberturaRegionReadRepository:
    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def count_unidades_activas(self, idregionoperativa: int) -> int:
        idscondado = self._condados_de_la_region(idregionoperativa)
        if not idscondado:
            return 0
        rows = self.pinot.query(
            """
            SELECT idunidademergencia FROM Dim_UnidadEmergencia
            WHERE idcondado IN %(idscondado)s AND activo = true
            """,
            {"idscondado": idscondado},
        )
        return len(rows)

    def _condados_de_la_region(self, idregionoperativa: int) -> list[int]:
        links = self.pinot.query(
            "SELECT idestadoregion FROM Dim_RegionOperativaEstadoRegion "
            "WHERE idregionoperativa = %(idregionoperativa)s",
            {"idregionoperativa": idregionoperativa},
        )
        idsestado = [row["idestadoregion"] for row in links]
        if not idsestado:
            return []
        condados = self.pinot.query(
            "SELECT idcondado FROM Dim_Condado WHERE idestado IN %(idsestado)s",
            {"idsestado": idsestado},
        )
        # Fallback: algunos seeds usan idestadoregion en lugar de idestado
        if not condados:
            condados = self.pinot.query(
                "SELECT idcondado FROM Dim_Condado WHERE idestadoregion IN %(idsestado)s",
                {"idsestado": idsestado},
            )
        return [row["idcondado"] for row in condados]
