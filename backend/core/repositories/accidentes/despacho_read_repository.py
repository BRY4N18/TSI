"""Fact_Despacho read-only repository for O40 preconditions."""

from __future__ import annotations

from core.pinot.client import PinotClient


class DespachoReadRepository:
    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def has_active_confirmed(self, idaccidente: str, idusuario: int | None = None) -> bool:
        rows = self.pinot.query(
            """
            SELECT iddespacho FROM Fact_Despacho
            WHERE idaccidente = %(idaccidente)s AND activo = true
            """,
            {"idaccidente": idaccidente},
        )
        return bool(rows)
