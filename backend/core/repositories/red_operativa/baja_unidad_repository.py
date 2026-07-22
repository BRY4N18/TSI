"""Fact_BajaUnidad repository — trazabilidad de bajas (CU-O58)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.red_operativa.kafka_writer import KafkaWriter


class BajaUnidadRepository:
    TOPIC = settings.KAFKA_TOPICS["baja_unidad"]

    def __init__(
        self,
        pinot: PinotClient | None = None,
        kafka: KafkaWriter | None = None,
    ):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def list_by_unidad(self, idunidademergencia: int) -> list[dict[str, Any]]:
        return self.pinot.query(
            "SELECT * FROM Fact_BajaUnidad WHERE idunidademergencia = %(idunidademergencia)s",
            {"idunidademergencia": idunidademergencia},
        )

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "idbajaunidad": self._next_id(),
            "idunidademergencia": data["idunidademergencia"],
            "idusuario": data["idusuario"],
            "idaccidente": data.get("idaccidente"),
            "motivo": data["motivo"],
            "tipobaja": data["tipobaja"],
            "fechahora": data.get("fechahora", now),
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def _next_id(self) -> int:
        rows = self.pinot.query("SELECT MAX(idbajaunidad) AS max_id FROM Fact_BajaUnidad")
        max_id = rows[0].get("max_id") if rows else 0
        return int(max_id or 0) + 1
