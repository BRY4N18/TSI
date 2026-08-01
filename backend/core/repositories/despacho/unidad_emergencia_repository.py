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
        tipounidademergencia: str | None = None,
        limit: int = 100,
        cursor: int | None = None,
    ) -> list[dict[str, Any]]:
        """Flota activa, paginada por keyset sobre `idunidademergencia`.

        El tipo de unidad se filtra por `tipounidademergencia` (texto:
        "Ambulancia", "Grúa", …), que es la columna que realmente existe en
        `Dim_UnidadEmergencia`. Antes se filtraba por un inexistente
        `idtipounidad`, así que cualquier filtro por tipo devolvía la flota
        vacía en vez de las unidades de ese tipo.
        """
        condiciones = ["activo = true"]
        params: dict[str, Any] = {"limit": limit}
        if tipounidademergencia is not None:
            condiciones.append("tipounidademergencia = %(tipo)s")
            params["tipo"] = tipounidademergencia
        if cursor is not None:
            condiciones.append("idunidademergencia > %(cursor)s")
            params["cursor"] = cursor
        return self.pinot.query(
            f"""
            SELECT * FROM Dim_UnidadEmergencia
            WHERE {' AND '.join(condiciones)}
            ORDER BY idunidademergencia
            LIMIT %(limit)s
            """,
            params,
        )

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
            if row.get("idcondado") in condados:
                candidatas.append(row)
        candidatas.sort(key=lambda r: r.get("idunidademergencia", 0))
        return candidatas
