"""Fact_Historial_Ticket repository — append-only Kafka writes (RNF-TIC-002)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.soporte.kafka_writer import KafkaWriter
from core.pinot.secuencia import siguiente_id


class HistorialTicketRepository:
    TOPIC = settings.KAFKA_TOPICS["historial_ticket"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _next_id(self) -> int:
        return siguiente_id(self.pinot, "Fact_Historial_Ticket", "id_historial")

    def list_by_ticket(self, id_reclamo: int) -> list[dict[str, Any]]:
        rows = self.pinot.query(
            "SELECT * FROM Fact_Historial_Ticket WHERE id_reclamo = %(id_reclamo)s",
            {"id_reclamo": id_reclamo},
        )
        rows.sort(key=lambda r: (r.get("fecha_accion", 0), r.get("id_historial", 0)))
        return rows

    def append(
        self,
        *,
        id_reclamo: int,
        tipo_accion: str,
        idusuario: int | None = None,
        mensaje: str | None = None,
        es_nota_interna: bool = False,
        estado_anterior: str | None = None,
        estado_nuevo: str | None = None,
    ) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            "id_historial": self._next_id(),
            "id_reclamo": id_reclamo,
            "tipo_accion": tipo_accion,
            "mensaje": mensaje,
            "es_nota_interna": es_nota_interna,
            "idusuario": idusuario,
            "estado_anterior": estado_anterior,
            "estado_nuevo": estado_nuevo,
            "fecha_accion": now,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload
