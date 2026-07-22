"""Fact_Accidente read-only repository (módulo Emergencias) — regla de continuidad (RF-REGON-003).

Resuelve la cobertura geográfica de una región (Dim_RegionOperativaEstadoRegion →
Dim_Condado → Dim_Ciudad → Dim_Calle) en la dirección inversa a la usada por
`core/repositories/accidentes/region_operativa_repository.py` (que resuelve
calle → región), para saber si existen accidentes activos dentro de una región.
"""

from __future__ import annotations

from core.pinot.client import PinotClient


class AccidenteActivoReadRepository:
    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def existen_casos_activos(self, idregionoperativa: int) -> bool:
        idscalle = self._calles_de_la_region(idregionoperativa)
        if not idscalle:
            return False
        rows = self.pinot.query(
            """
            SELECT idaccidente FROM Fact_Accidente
            WHERE idcalle IN %(idscalle)s AND activo = true
            LIMIT 1
            """,
            {"idscalle": idscalle},
        )
        return bool(rows)

    def _calles_de_la_region(self, idregionoperativa: int) -> list[int]:
        links = self.pinot.query(
            "SELECT idestadoregion FROM Dim_RegionOperativaEstadoRegion WHERE idregionoperativa = %(idregionoperativa)s",
            {"idregionoperativa": idregionoperativa},
        )
        idsestado = [row["idestadoregion"] for row in links]
        if not idsestado:
            return []

        condados = self.pinot.query(
            "SELECT idcondado FROM Dim_Condado WHERE idestado IN %(idsestado)s",
            {"idsestado": idsestado},
        )
        idscondado = [row["idcondado"] for row in condados]
        if not idscondado:
            return []

        ciudades = self.pinot.query(
            "SELECT idciudad FROM Dim_Ciudad WHERE idcondado IN %(idscondado)s",
            {"idscondado": idscondado},
        )
        idsciudad = [row["idciudad"] for row in ciudades]
        if not idsciudad:
            return []

        calles = self.pinot.query(
            "SELECT idcalle FROM Dim_Calle WHERE idciudad IN %(idsciudad)s",
            {"idsciudad": idsciudad},
        )
        return [row["idcalle"] for row in calles]
