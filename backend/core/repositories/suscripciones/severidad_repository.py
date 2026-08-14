"""Dim_Severidad — catálogo de severidades de accidente (solo lectura).

Existe porque el catálogo vivía duplicado: `Dim_Severidad` en base de datos, una
escala paralela `{"Baja","Media","Alta"}` en `catalogo_plan_service` y un
diccionario puente en `partners`. Las tres divergían. Este repositorio es la
única puerta de lectura del catálogo real.
"""

from __future__ import annotations

from typing import Any

from core.pinot.client import PinotClient


class SeveridadRepository:
    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def listar_activas(self) -> list[dict[str, Any]]:
        """Severidades vigentes, de la más leve a la más grave."""
        rows = self.pinot.query(
            "SELECT idseveridad, severidad, descripcion FROM Dim_Severidad "
            "WHERE activo = true ORDER BY idseveridad ASC LIMIT 100"
        ) or []
        return [
            {
                "idseveridad": int(row["idseveridad"]),
                "severidad": row["severidad"],
                "descripcion": row.get("descripcion"),
            }
            for row in rows
        ]

    def ids_validos(self) -> set[int]:
        return {item["idseveridad"] for item in self.listar_activas()}

    def nombres_por_id(self) -> dict[int, str]:
        return {item["idseveridad"]: item["severidad"] for item in self.listar_activas()}
