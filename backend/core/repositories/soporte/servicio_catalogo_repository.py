"""Catálogo Dim_Servicio (FK opcional Fact_Reclamo.idservicio)."""

from __future__ import annotations

from core.pinot.client import PinotClient


class ServicioCatalogoRepository:
    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def listar_activos(self) -> list[dict]:
        rows = self.pinot.query(
            """
            SELECT id_servicio AS id, nombre
            FROM Dim_Servicio
            WHERE activo = true
            ORDER BY nombre
            """,
            {},
        )
        return rows
