"""Dim_Plan repository — catálogo de planes (RF-SUSF-001)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.suscripciones.kafka_writer import KafkaWriter


class PlanRepository:
    TOPIC = settings.KAFKA_TOPICS["plan"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _now_ms(self) -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000)

    def _next_id(self) -> int:
        rows = self.pinot.query("SELECT MAX(idplan) AS max_id FROM Dim_Plan", {})
        return int(rows[0]["max_id"] or 0) + 1 if rows else 1

    def find_by_id(self, idplan: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Dim_Plan WHERE idplan = %(idplan)s",
            {"idplan": idplan},
        )
        return rows[0] if rows else None

    def list(self, *, solo_activos: bool = True) -> list[dict[str, Any]]:
        rows = list(self.pinot.query("SELECT * FROM Dim_Plan", {}) or [])
        if solo_activos:
            rows = [r for r in rows if r.get("activo")]
        rows.sort(key=lambda r: r.get("idplan", 0))
        return rows

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        limites = data.get("limites", {})
        if isinstance(limites, dict):
            limites = json.dumps(limites, ensure_ascii=False)
        record = {
            "idplan": self._next_id(),
            "nombre": data["nombre"],
            "precio": float(data["precio"]),
            "limites": limites,
            "nivel": data["nivel"],
            "activo": True,
            "fecha_actualizacion": self._now_ms(),
        }
        self.kafka.publish(self.TOPIC, record)
        return record

    def update(self, idplan: int, changes: dict[str, Any]) -> dict[str, Any] | None:
        current = self.find_by_id(idplan)
        if not current:
            return None
        payload = {**current, **changes, "fecha_actualizacion": self._now_ms()}
        if isinstance(payload.get("limites"), dict):
            payload["limites"] = json.dumps(payload["limites"], ensure_ascii=False)
        self.kafka.publish(self.TOPIC, payload)
        return payload
