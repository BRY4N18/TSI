"""Dim_UnidadEmergencia snapshot — Kafka write for GPS position."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.accidentes.kafka_writer import KafkaWriter


class UnidadSnapshotRepository:
    TOPIC = settings.KAFKA_TOPICS["unidad_emergencia_snapshot"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def publish_snapshot(
        self,
        *,
        idunidademergencia: int,
        latitud: float,
        longitud: float,
        fechahora: int | None = None,
    ) -> dict[str, Any]:
        now = fechahora or int(datetime.now(timezone.utc).timestamp() * 1000)
        existing = self.pinot.query(
            """
            SELECT * FROM Dim_UnidadEmergencia
            WHERE idunidademergencia = %(idunidademergencia)s
            LIMIT 1
            """,
            {"idunidademergencia": idunidademergencia},
        )
        base = existing[0] if existing else {"idunidademergencia": idunidademergencia}
        payload = {
            **base,
            "idunidademergencia": idunidademergencia,
            "latitud": latitud,
            "longitud": longitud,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload
