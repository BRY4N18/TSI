"""Geografía condado — resolución desde idcalle y condados vecinos."""

from __future__ import annotations

from core.pinot.client import PinotClient


class GeografiaRepository:
    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def resolve_condado_from_idcalle(self, idcalle: int) -> int | None:
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
        return int(ciudades[0]["idcondado"]) if ciudades else None

    def list_condados_vecinos(self, idcondado: int) -> list[int]:
        rows = self.pinot.query(
            """
            SELECT idcondadovecino
            FROM Dim_CondadoVecino
            WHERE idcondado = %(idcondado)s
            """,
            {"idcondado": idcondado},
        )
        return [int(r["idcondadovecino"]) for r in rows]
