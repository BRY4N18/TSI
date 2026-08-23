"""Dim_Conductor repository — Pinot read, Kafka write."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.accidentes.kafka_writer import KafkaWriter
from core.pinot.secuencia import siguiente_id


class ConductorRepository:
    TOPIC = settings.KAFKA_TOPICS["conductor"]

    def __init__(
        self,
        pinot: PinotClient | None = None,
        kafka: KafkaWriter | None = None,
    ):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _next_id(self) -> int:
        return siguiente_id(self.pinot, "Dim_Conductor", "idconductor")

    def find_by_id(self, idconductor: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_Conductor
            WHERE idconductor = %(id)s
            LIMIT 1
            """,
            {"id": idconductor},
        )
        return rows[0] if rows else None

    def find_by_identificacion(self, identificacion: str) -> dict[str, Any] | None:
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_Conductor
            WHERE identificacion = %(identificacion)s
            """,
            {"identificacion": identificacion},
        )
        activos = [r for r in rows if r.get("activo", True)]
        return activos[0] if activos else None

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            "idconductor": self._next_id(),
            "apellidos": data["apellidos"],
            "nombres": data["nombres"],
            "identificacion": data["identificacion"],
            "genero": data.get("genero"),
            "tipolicencia": data.get("tipolicencia"),
            "estadolicencia": data.get("estadolicencia"),
            "ciudadresidencia": data.get("ciudadresidencia"),
            "aniosexperiencia": data.get("aniosexperiencia"),
            "activo": True,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload
