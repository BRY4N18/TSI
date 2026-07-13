"""Dim_RegionOperativa coverage checks."""

from __future__ import annotations

from core.pinot.client import PinotClient


class RegionOperativaRepository:
    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def is_estado_en_produccion(self, idestadoregion: int) -> bool:
        links = self.pinot.query(
            "SELECT idregionoperativa FROM Dim_RegionOperativaEstadoRegion WHERE idestadoregion = %(idestadoregion)s",
            {"idestadoregion": idestadoregion},
        )
        region_ids = [row["idregionoperativa"] for row in links]
        if not region_ids:
            return False
        rows = self.pinot.query(
            """
            SELECT idregionoperativa FROM Dim_RegionOperativa
            WHERE idregionoperativa IN %(region_ids)s
              AND estadoregion = 'Producción'
              AND activo = true
            LIMIT 1
            """,
            {"region_ids": region_ids},
        )
        return bool(rows)

    def resolve_estado_from_calle(self, idcalle: int) -> int | None:
        calles = self.pinot.query(
            "SELECT idciudad FROM Dim_Calle WHERE idcalle = %(idcalle)s LIMIT 1",
            {"idcalle": idcalle},
        )
        if not calles:
            return None
        ciudades = self.pinot.query(
            "SELECT idcondado FROM Dim_Ciudad WHERE idciudad = %(idciudad)s LIMIT 1",
            {"idciudad": calles[0]["idciudad"]},
        )
        if not ciudades:
            return None
        condados = self.pinot.query(
            "SELECT idestado FROM Dim_Condado WHERE idcondado = %(idcondado)s LIMIT 1",
            {"idcondado": ciudades[0]["idcondado"]},
        )
        return int(condados[0]["idestado"]) if condados else None
