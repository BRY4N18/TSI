"""Fact_Solicitud_Cambio_Plan repository — RF-SUSF-003."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.suscripciones.kafka_writer import KafkaWriter


class SolicitudCambioPlanRepository:
    TOPIC = settings.KAFKA_TOPICS["solicitud_cambio_plan"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _now_ms(self) -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000)

    def _next_id(self) -> int:
        rows = self.pinot.query(
            "SELECT MAX(idsolicitud) AS max_id FROM Fact_Solicitud_Cambio_Plan", {}
        )
        return int(rows[0]["max_id"] or 0) + 1 if rows else 1

    def find_by_id(self, idsolicitud: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Fact_Solicitud_Cambio_Plan WHERE idsolicitud = %(id)s",
            {"id": idsolicitud},
        )
        return rows[0] if rows else None

    def find_pendiente(self, idcliente: int) -> dict[str, Any] | None:
        rows = list(self.pinot.query("SELECT * FROM Fact_Solicitud_Cambio_Plan", {}) or [])
        for r in rows:
            if r.get("idcliente") == idcliente and r.get("estado") == "Pendiente":
                return r
        return None

    def list(
        self,
        *,
        idcliente: int | None = None,
        estado: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        rows = list(self.pinot.query("SELECT * FROM Fact_Solicitud_Cambio_Plan", {}) or [])
        if idcliente is not None:
            rows = [r for r in rows if r.get("idcliente") == idcliente]
        if estado:
            rows = [r for r in rows if r.get("estado") == estado]
        rows.sort(key=lambda r: r.get("idsolicitud", 0), reverse=True)
        return rows[:limit]

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        record = {
            "idsolicitud": self._next_id(),
            "idcliente": data["idcliente"],
            "idplanactual": data["idplanactual"],
            "idplansolicitado": data["idplansolicitado"],
            "estado": data.get("estado", "Pendiente"),
            "motivo": data.get("motivo", ""),
            "motivo_rechazo": None,
            "idadminaprobador": data.get("idadminaprobador"),
            "fecha_solicitud": self._now_ms(),
            "fecha_resolucion": data.get("fecha_resolucion"),
            "fecha_actualizacion": self._now_ms(),
        }
        self.kafka.publish(self.TOPIC, record)
        return record

    def update(self, idsolicitud: int, changes: dict[str, Any]) -> dict[str, Any] | None:
        current = self.find_by_id(idsolicitud)
        if not current:
            return None
        payload = {**current, **changes, "fecha_actualizacion": self._now_ms()}
        self.kafka.publish(self.TOPIC, payload)
        return payload
