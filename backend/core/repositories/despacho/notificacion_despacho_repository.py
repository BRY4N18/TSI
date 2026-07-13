"""Fact_NotificacionDespacho repository — Pinot read, Kafka write."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.accidentes.kafka_writer import KafkaWriter

ESTADO_PENDIENTE = "Pendiente"
ESTADO_NOTIFICADA = "Notificada"
ESTADO_CONFIRMADA = "Confirmada"
ESTADO_RECHAZADA = "Rechazada"
ESTADO_NO_ENTREGADA = "No_entregada"


class NotificacionDespachoRepository:
    TOPIC = settings.KAFKA_TOPICS["notificacion_despacho"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _next_id(self) -> int:
        rows = self.pinot.query(
            "SELECT MAX(idnotificaciondespacho) AS max_id FROM Fact_NotificacionDespacho",
            {},
        )
        return int(rows[0]["max_id"] or 0) + 1 if rows else 1

    def find_by_id(self, idnotificaciondespacho: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            """
            SELECT * FROM Fact_NotificacionDespacho
            WHERE idnotificaciondespacho = %(idnotificaciondespacho)s
            LIMIT 1
            """,
            {"idnotificaciondespacho": idnotificaciondespacho},
        )
        return rows[0] if rows else None

    def list_by_accidente(self, idaccidente: str) -> list[dict[str, Any]]:
        rows = self.pinot.query(
            """
            SELECT * FROM Fact_NotificacionDespacho
            WHERE idaccidente = %(idaccidente)s
            """,
            {"idaccidente": idaccidente},
        )
        rows.sort(key=lambda r: r.get("fecha_actualizacion", 0))
        return rows

    def list_by_unidad(self, idunidademergencia: int, *, activo: bool = True) -> list[dict[str, Any]]:
        rows = self.pinot.query(
            """
            SELECT * FROM Fact_NotificacionDespacho
            WHERE idunidaddemergencia = %(idunidaddemergencia)s
            """,
            {"idunidaddemergencia": idunidademergencia},
        )
        if activo:
            rows = [r for r in rows if r.get("activo")]
        rows.sort(key=lambda r: r.get("fecha_actualizacion", 0), reverse=True)
        return rows

    def publish_create(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        record = {
            **payload,
            "idnotificaciondespacho": payload.get("idnotificaciondespacho", self._next_id()),
            "estadonotificaciondespacho": payload.get(
                "estadonotificaciondespacho", ESTADO_PENDIENTE
            ),
            "fecha_actualizacion": now,
            "activo": payload.get("activo", True),
        }
        self.kafka.publish(self.TOPIC, record)
        return record

    def publish_update(
        self, idnotificaciondespacho: int, fields: dict[str, Any]
    ) -> dict[str, Any] | None:
        current = self.find_by_id(idnotificaciondespacho)
        if not current:
            return None
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        updated = {**current, **fields, "fecha_actualizacion": now}
        self.kafka.publish(self.TOPIC, updated)
        return updated
