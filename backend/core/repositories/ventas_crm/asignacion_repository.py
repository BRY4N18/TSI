"""Fact_Asignacion read and Kafka append-only writer."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from django.conf import settings
from core.pinot.client import PinotClient
from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter


class AsignacionRepository:
    TOPIC = settings.KAFKA_TOPICS["asignacion"]
    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot, self.kafka = pinot or PinotClient(), kafka or KafkaWriter()
    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {**data, "idasignacion": self._next_id(), "fechahoraasignacion": now, "fecha_actualizacion": now}
        self.kafka.publish(self.TOPIC, payload); return payload
    def list_by_prospecto(self, idprospecto: int) -> list[dict[str, Any]]:
        return list(self.pinot.query("SELECT * FROM Fact_Asignacion WHERE idprospecto = %(id)s ORDER BY idasignacion", {"id": idprospecto}) or [])
    def _next_id(self) -> int:
        rows = self.pinot.query("SELECT MAX(idasignacion) AS max_id FROM Fact_Asignacion")
        return int((rows[0].get("max_id") or 0) if rows else 0) + 1
