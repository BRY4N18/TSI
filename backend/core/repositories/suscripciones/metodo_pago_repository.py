"""Dim_MetodoPago repository — RF-SUSF-002."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.suscripciones.kafka_writer import KafkaWriter


class MetodoPagoRepository:
    TOPIC = settings.KAFKA_TOPICS["metodo_pago"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _now_ms(self) -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000)

    def _next_id(self) -> int:
        rows = self.pinot.query("SELECT MAX(idmetodopago) AS max_id FROM Dim_MetodoPago", {})
        return int(rows[0]["max_id"] or 0) + 1 if rows else 1

    def find_by_id(self, idmetodopago: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Dim_MetodoPago WHERE idmetodopago = %(id)s",
            {"id": idmetodopago},
        )
        return rows[0] if rows else None

    def list_by_cliente(self, idcliente: int) -> list[dict[str, Any]]:
        rows = list(self.pinot.query("SELECT * FROM Dim_MetodoPago", {}) or [])
        return [r for r in rows if r.get("idcliente") == idcliente]

    def find_activo(self, idcliente: int) -> dict[str, Any] | None:
        for row in self.list_by_cliente(idcliente):
            if row.get("activo"):
                return row
        return None

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        record = {
            "idmetodopago": self._next_id(),
            "idcliente": data["idcliente"],
            "tipo": data["tipo"],
            "tokenpasarela": data["tokenpasarela"],
            "ultimosdigitos": data.get("ultimosdigitos", "")[:4],
            "fechaexpiracion": data.get("fechaexpiracion"),
            "activo": True,
            "fecha_actualizacion": self._now_ms(),
        }
        self.kafka.publish(self.TOPIC, record)
        return record

    def update(self, idmetodopago: int, changes: dict[str, Any]) -> dict[str, Any] | None:
        current = self.find_by_id(idmetodopago)
        if not current:
            return None
        payload = {**current, **changes, "fecha_actualizacion": self._now_ms()}
        self.kafka.publish(self.TOPIC, payload)
        return payload
