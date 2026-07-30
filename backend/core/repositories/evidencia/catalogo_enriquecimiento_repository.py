"""Catálogos de lectura para enriquecimiento CU-O46."""

from __future__ import annotations

from typing import Any

from core.pinot.client import PinotClient


class CatalogoEnriquecimientoRepository:
    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def list_periodos_dias(self) -> list[dict[str, Any]]:
        rows = self.pinot.query("SELECT * FROM Dim_PeriodosDias", {})
        return [r for r in rows if r.get("activo", True)]

    def list_estados_climas(self) -> list[dict[str, Any]]:
        rows = self.pinot.query("SELECT * FROM Dim_EstadosClimas", {})
        return [r for r in rows if r.get("activo", True)]

    def list_elementos_fisicos(self) -> list[dict[str, Any]]:
        rows = self.pinot.query("SELECT * FROM Dim_Elementos_Fisicos", {})
        return [r for r in rows if r.get("activo", True)]

    def list_estados_conductor(self) -> list[dict[str, Any]]:
        rows = self.pinot.query("SELECT * FROM Dim_Estado_Conductor", {})
        return [r for r in rows if r.get("activo", True)]

    def find_elemento_fisico(self, idelementofisico: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_Elementos_Fisicos
            WHERE idelementofisico = %(id)s
            LIMIT 1
            """,
            {"id": idelementofisico},
        )
        return rows[0] if rows else None

    def find_estado_conductor(self, idestadoconductor: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_Estado_Conductor
            WHERE idestadoconductor = %(id)s
            LIMIT 1
            """,
            {"id": idestadoconductor},
        )
        return rows[0] if rows else None

    def find_periodo(self, idperiododia: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_PeriodosDias
            WHERE idperiododia = %(id)s
            LIMIT 1
            """,
            {"id": idperiododia},
        )
        return rows[0] if rows else None

    def find_estado_clima(self, idestadoclima: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_EstadosClimas
            WHERE idestadoclima = %(id)s
            LIMIT 1
            """,
            {"id": idestadoclima},
        )
        return rows[0] if rows else None
