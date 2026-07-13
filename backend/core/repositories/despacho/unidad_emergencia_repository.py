"""Dim_UnidadEmergencia read repository."""

from __future__ import annotations

from typing import Any

from core.pinot.client import PinotClient


class UnidadEmergenciaRepository:
    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def find_by_id(self, idunidademergencia: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_UnidadEmergencia
            WHERE idunidademergencia = %(idunidademergencia)s
            LIMIT 1
            """,
            {"idunidademergencia": idunidademergencia},
        )
        return rows[0] if rows else None

    def find_by_usuario(self, idusuario: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_UnidadEmergencia
            WHERE idusuario = %(idusuario)s AND activo = true
            LIMIT 1
            """,
            {"idusuario": idusuario},
        )
        return rows[0] if rows else None

    def list_active(
        self,
        *,
        idtipounidad: int | None = None,
        limit: int = 100,
        cursor: int | None = None,
    ) -> list[dict[str, Any]]:
        rows = self.pinot.query(
            "SELECT * FROM Dim_UnidadEmergencia WHERE activo = true",
            {},
        )
        if idtipounidad is not None:
            rows = [r for r in rows if r.get("idtipounidad") == idtipounidad]
        rows.sort(key=lambda r: r.get("idunidademergencia", 0))
        if cursor is not None:
            rows = [r for r in rows if r.get("idunidademergencia", 0) > cursor]
        return rows[:limit]

    def list_candidatas_por_condado(
        self,
        idcondado: int,
        *,
        idcondados_extra: list[int] | None = None,
    ) -> list[dict[str, Any]]:
        condados = {idcondado}
        if idcondados_extra:
            condados.update(idcondados_extra)
        rows = self.pinot.query(
            "SELECT * FROM Dim_UnidadEmergencia WHERE activo = true",
            {},
        )
        candidatas = []
        for row in rows:
            row_condado = row.get("idcondado")
            if row_condado is None and row.get("zonacobertura") is not None:
                try:
                    row_condado = int(row["zonacobertura"])
                except (TypeError, ValueError):
                    row_condado = None
            if row_condado in condados:
                candidatas.append(row)
        candidatas.sort(key=lambda r: r.get("idunidademergencia", 0))
        return candidatas
