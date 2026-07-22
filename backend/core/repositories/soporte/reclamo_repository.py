"""Fact_Reclamo repository — el ticket de soporte (CU-O91, O92, O96, O97)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.soporte.kafka_writer import KafkaWriter


class ReclamoRepository:
    TOPIC = settings.KAFKA_TOPICS["reclamo"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _next_id(self) -> int:
        rows = self.pinot.query("SELECT MAX(id_reclamo) AS max_id FROM Fact_Reclamo", {})
        return int(rows[0]["max_id"] or 0) + 1 if rows else 1

    def _resolve_idestadosoporte(self, nombre: str | None) -> int | None:
        """RN-TIC-007 — `idestadosoporte` y `estado` (denormalizado) deben ser consistentes."""
        if not nombre:
            return None
        rows = self.pinot.query(
            "SELECT * FROM Dim_Estado_Soporte WHERE nombre = %(nombre)s", {"nombre": nombre}
        )
        return rows[0]["id_estado_soporte"] if rows else None

    def _con_estado_consistente(self, data: dict[str, Any]) -> dict[str, Any]:
        if "estado" in data:
            data = {**data, "idestadosoporte": self._resolve_idestadosoporte(data["estado"])}
        return data

    def find_by_id(self, id_reclamo: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Fact_Reclamo WHERE id_reclamo = %(id_reclamo)s",
            {"id_reclamo": id_reclamo},
        )
        return rows[0] if rows else None

    def list(
        self,
        *,
        idestadosoporte: str | None = None,
        prioridad: str | None = None,
        idcliente: int | None = None,
        limit: int = 20,
        cursor: int | None = None,
    ) -> list[dict[str, Any]]:
        rows = self.pinot.query("SELECT * FROM Fact_Reclamo", {})
        if idestadosoporte:
            rows = [r for r in rows if r.get("estado") == idestadosoporte]
        if prioridad:
            rows = [r for r in rows if r.get("prioridad") == prioridad]
        if idcliente is not None:
            rows = [r for r in rows if r.get("idcliente") == idcliente]
        rows.sort(key=lambda r: r.get("id_reclamo", 0), reverse=True)
        if cursor is not None:
            rows = [r for r in rows if r.get("id_reclamo", 0) < cursor]
        return rows[:limit]

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        record = {
            "id_reclamo": self._next_id(),
            "activo": True,
            "fechahora": now,
            "fecha_actualizacion": now,
            **self._con_estado_consistente(payload),
        }
        self.kafka.publish(self.TOPIC, record)
        return record

    def update(self, id_reclamo: int, changes: dict[str, Any]) -> dict[str, Any]:
        current = self.find_by_id(id_reclamo)
        if not current:
            raise LookupError(f"Ticket {id_reclamo} no encontrado")
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        record = {**current, **self._con_estado_consistente(changes), "fecha_actualizacion": now}
        self.kafka.publish(self.TOPIC, record)
        return record
