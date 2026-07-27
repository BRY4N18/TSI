"""Read-only Pinot repository for Dim_Plan (RF-CPP-000). Never publishes to Kafka."""
from __future__ import annotations

from typing import Any

from core.pinot.client import PinotClient


class PlanLecturaRepository:
    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def list_activos(self) -> list[dict[str, Any]]:
        return list(
            self.pinot.query(
                "SELECT * FROM Dim_Plan WHERE activo = true ORDER BY idplan",
                {},
            )
            or []
        )
