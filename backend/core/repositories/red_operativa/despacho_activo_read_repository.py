"""Fact_Despacho read-only repository (módulo Emergencias) — usado para bloqueo de edición/baja."""

from __future__ import annotations

from core.pinot.client import PinotClient


class DespachoActivoReadRepository:
    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def has_despacho_activo(self, idunidademergencia: int) -> bool:
        rows = self.pinot.query(
            """
            SELECT iddespacho FROM Fact_Despacho
            WHERE idunidademergencia = %(idunidademergencia)s AND activo = true
            LIMIT 1
            """,
            {"idunidademergencia": idunidademergencia},
        )
        return bool(rows)

    def find_despacho_activo(self, idunidademergencia: int) -> dict | None:
        rows = self.pinot.query(
            """
            SELECT * FROM Fact_Despacho
            WHERE idunidademergencia = %(idunidademergencia)s AND activo = true
            LIMIT 1
            """,
            {"idunidademergencia": idunidademergencia},
        )
        return rows[0] if rows else None
