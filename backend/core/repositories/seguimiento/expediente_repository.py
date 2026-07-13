"""Consultas de historial y expedientes — Pinot read."""

from __future__ import annotations

from typing import Any

from core.pinot.client import PinotClient


class ExpedienteRepository:
    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def list_accidentes(
        self,
        *,
        estado: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        rows = self.pinot.query(
            """
            SELECT idaccidente, horainicio, idseveridad, latitudinicio, longitudinicio, idcalle
            FROM Fact_Accidente
            """,
            {},
        )
        if estado:
            filtered: list[dict[str, Any]] = []
            for row in rows:
                est_rows = self.pinot.query(
                    """
                    SELECT estado FROM Fact_AccidenteTipoEstadoAccidente
                    WHERE idaccidente = %(idaccidente)s
                    ORDER BY fechahoramodificado DESC
                    LIMIT 1
                    """,
                    {"idaccidente": row["idaccidente"]},
                )
                if est_rows and est_rows[0].get("estado") == estado:
                    filtered.append(row)
            rows = filtered
        rows.sort(key=lambda r: r.get("horainicio", 0), reverse=True)
        return rows[:limit]

    def find_accidente(self, idaccidente: str) -> dict[str, Any] | None:
        rows = self.pinot.query(
            """
            SELECT * FROM Fact_Accidente
            WHERE idaccidente = %(idaccidente)s
            LIMIT 1
            """,
            {"idaccidente": idaccidente},
        )
        return rows[0] if rows else None
