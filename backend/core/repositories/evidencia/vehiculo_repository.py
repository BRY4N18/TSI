"""Dim_Vehiculo repository — Pinot read, Kafka write."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.accidentes.kafka_writer import KafkaWriter
from core.pinot.secuencia import siguiente_id


class VehiculoRepository:
    TOPIC = settings.KAFKA_TOPICS["vehiculo"]

    def __init__(
        self,
        pinot: PinotClient | None = None,
        kafka: KafkaWriter | None = None,
    ):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _next_id(self) -> int:
        return siguiente_id(self.pinot, "Dim_Vehiculo", "idvehiculo")

    def find_by_id(self, idvehiculo: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_Vehiculo
            WHERE idvehiculo = %(id)s
            LIMIT 1
            """,
            {"id": idvehiculo},
        )
        return rows[0] if rows else None

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            "idvehiculo": self._next_id(),
            "tipovehiculo": data["tipovehiculo"],
            "modelovehiculo": data.get("modelovehiculo"),
            "categoriausovehiculo": data.get("categoriausovehiculo"),
            "mercanciapeligrosa": data.get("mercanciapeligrosa"),
            "ejes": data.get("ejes"),
            "activo": True,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload
