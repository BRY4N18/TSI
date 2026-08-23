"""Fact_ArchivosAdjuntosReclamos repository (RF-TIC-001 paso 5, RF-TIC-005 paso 4)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.soporte.kafka_writer import KafkaWriter
from core.pinot.secuencia import siguiente_id


class ArchivoAdjuntoReclamoRepository:
    TOPIC = settings.KAFKA_TOPICS["archivo_adjunto_reclamo"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _next_id(self) -> int:
        return siguiente_id(self.pinot, "Fact_ArchivosAdjuntosReclamos", "idarchivoadjuntoreclamo")

    def list_by_ticket(self, id_reclamo: int) -> list[dict[str, Any]]:
        return self.pinot.query(
            "SELECT * FROM Fact_ArchivosAdjuntosReclamos WHERE id_reclamo = %(id_reclamo)s",
            {"id_reclamo": id_reclamo},
        )

    def append(self, *, id_reclamo: int, urlarchivo: str) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            "idarchivoadjuntoreclamo": self._next_id(),
            "id_reclamo": id_reclamo,
            "urlarchivo": urlarchivo,
            "activo": True,
            "fechahorasubida": now,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload
