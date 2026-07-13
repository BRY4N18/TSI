"""Fact_Despacho repository — Pinot read, Kafka write."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.accidentes.kafka_writer import KafkaWriter


class DespachoRepository:
    TOPIC = settings.KAFKA_TOPICS["despacho"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _next_id(self) -> int:
        rows = self.pinot.query(
            "SELECT MAX(iddespacho) AS max_id FROM Fact_Despacho",
            {},
        )
        return int(rows[0]["max_id"] or 0) + 1 if rows else 1

    def find_by_id(self, iddespacho: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            """
            SELECT * FROM Fact_Despacho
            WHERE iddespacho = %(iddespacho)s
            LIMIT 1
            """,
            {"iddespacho": iddespacho},
        )
        return rows[0] if rows else None

    def list_by_accidente(
        self,
        idaccidente: str,
        *,
        activo: bool | None = None,
    ) -> list[dict[str, Any]]:
        rows = self.pinot.query(
            """
            SELECT * FROM Fact_Despacho
            WHERE idaccidente = %(idaccidente)s
            """,
            {"idaccidente": idaccidente},
        )
        if activo is not None:
            rows = [r for r in rows if r.get("activo") == activo]
        rows.sort(key=lambda r: r.get("fechahoradespacho", 0))
        return rows

    def list_activos_by_unidad(self, idunidademergencia: int) -> list[dict[str, Any]]:
        rows = self.pinot.query(
            """
            SELECT * FROM Fact_Despacho
            WHERE idunidademergencia = %(idunidademergencia)s AND activo = true
            """,
            {"idunidademergencia": idunidademergencia},
        )
        return rows

    def has_active_for_unidad(self, idunidademergencia: int) -> bool:
        return bool(self.list_activos_by_unidad(idunidademergencia))

    def list_all_active(self) -> list[dict[str, Any]]:
        rows = self.pinot.query(
            "SELECT * FROM Fact_Despacho WHERE activo = true",
            {},
        )
        rows.sort(key=lambda r: r.get("fechahoradespacho", 0))
        return rows

    def publish_create(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        record = {
            **payload,
            "iddespacho": payload.get("iddespacho", self._next_id()),
            "fechahoradespacho": payload.get("fechahoradespacho", now),
            "fecha_actualizacion": now,
            "activo": payload.get("activo", True),
        }
        self.kafka.publish(self.TOPIC, record)
        return record

    def publish_update(self, iddespacho: int, fields: dict[str, Any]) -> dict[str, Any] | None:
        current = self.find_by_id(iddespacho)
        if not current:
            return None
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        updated = {**current, **fields, "fecha_actualizacion": now}
        self.kafka.publish(self.TOPIC, updated)
        return updated
