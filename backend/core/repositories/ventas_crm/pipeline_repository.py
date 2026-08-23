"""Fact_Pipeline read and Kafka append-only writer."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from django.conf import settings
from core.pinot.client import PinotClient
from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter
from core.pinot.secuencia import siguiente_id


class PipelineRepository:
    TOPIC = settings.KAFKA_TOPICS["pipeline"]
    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot, self.kafka = pinot or PinotClient(), kafka or KafkaWriter()
    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {**data, "id_transicion": self._next_id(), "fecha_transicion": now, "fecha_actualizacion": now}
        self.kafka.publish(self.TOPIC, payload); return payload
    def list_by_prospecto(self, idprospecto: int) -> list[dict[str, Any]]:
        return list(self.pinot.query("SELECT * FROM Fact_Pipeline WHERE id_prospecto = %(id)s ORDER BY id_transicion", {"id": idprospecto}) or [])
    def _next_id(self) -> int:
        return siguiente_id(self.pinot, "Fact_Pipeline", "id_transicion")
