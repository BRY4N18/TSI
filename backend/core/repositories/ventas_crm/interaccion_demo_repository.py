"""Fact_Interaccion_Demo — Pinot read + Kafka-only write."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter
from core.pinot.secuencia import siguiente_id


class InteraccionDemoRepository:
    TOPIC = settings.KAFKA_TOPICS["interaccion_demo"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            **data,
            "idinteraccion": self._next_id(),
            "fecha_actualizacion": now,
        }
        if "timestamp_evento" not in payload:
            payload["timestamp_evento"] = now
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def list_by_prospecto(self, idprospecto: int) -> list[dict[str, Any]]:
        return list(
            self.pinot.query(
                "SELECT * FROM Fact_Interaccion_Demo WHERE idprospecto = %(id)s "
                "ORDER BY timestamp_evento",
                {"id": idprospecto},
            )
            or []
        )

    def list_inicio_sesion_recent(self, since_epoch_ms: int) -> list[dict[str, Any]]:
        return list(
            self.pinot.query(
                "SELECT * FROM Fact_Interaccion_Demo WHERE tipo_evento = %(tipo)s "
                "AND timestamp_evento >= %(since)s ORDER BY timestamp_evento",
                {"tipo": "inicio_sesion", "since": since_epoch_ms},
            )
            or []
        )

    def _next_id(self) -> int:
        return siguiente_id(self.pinot, "Fact_Interaccion_Demo", "idinteraccion")
