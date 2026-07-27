"""Pinot read and Kafka-only write repository for commercial prospects."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings
from core.pinot.client import PinotClient
from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter


class ProspectoRepository:
    TOPIC = settings.KAFKA_TOPICS["prospecto"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot, self.kafka = pinot or PinotClient(), kafka or KafkaWriter()

    def find_by_id(self, idprospecto: int) -> dict[str, Any] | None:
        rows = self.pinot.query("SELECT * FROM Dim_Prospecto WHERE idprospecto = %(id)s LIMIT 1", {"id": idprospecto})
        return rows[0] if rows else None

    def find_by_gmail(self, gmail: str) -> dict[str, Any] | None:
        rows = self.pinot.query("SELECT * FROM Dim_Prospecto WHERE gmail = %(gmail)s LIMIT 1", {"gmail": gmail})
        return rows[0] if rows else None

    def list(self, *, owner_id: int | None = None, activo: bool | None = None,
             etapa_actual: str | None = None, limit: int = 20, cursor: int | None = None) -> list[dict[str, Any]]:
        clauses, params = ["1 = 1"], {"limit": limit}
        if owner_id is not None: clauses.append("idusuario = %(owner_id)s"); params["owner_id"] = owner_id
        if activo is not None: clauses.append("activo = %(activo)s"); params["activo"] = activo
        if etapa_actual: clauses.append("etapa_actual = %(etapa)s"); params["etapa"] = etapa_actual
        if cursor: clauses.append("idprospecto > %(cursor)s"); params["cursor"] = cursor
        return list(self.pinot.query(f"SELECT * FROM Dim_Prospecto WHERE {' AND '.join(clauses)} ORDER BY idprospecto LIMIT %(limit)s", params) or [])

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {**data, "idprospecto": self._next_id(), "etapa_actual": "Nuevo", "idusuario": None,
                   "activo": True, "motivo_inactividad": None, "fecha_registro": now, "fecha_actualizacion": now}
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def update(self, idprospecto: int, data: dict[str, Any]) -> dict[str, Any] | None:
        current = self.find_by_id(idprospecto)
        if not current: return None
        payload = {**current, **data, "idprospecto": idprospecto,
                   "fecha_actualizacion": int(datetime.now(timezone.utc).timestamp() * 1000)}
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def update_demo_expiracion(self, idprospecto: int, iso_utc: str) -> dict[str, Any] | None:
        """Partial domain update: only demo_expiracion (+ fecha_actualizacion)."""
        return self.update(idprospecto, {"demo_expiracion": iso_utc})

    def count_active_by_user(self, user_id: int) -> int:
        rows = self.pinot.query("SELECT COUNT(*) AS count FROM Dim_Prospecto WHERE idusuario = %(id)s AND activo = true", {"id": user_id})
        return int((rows[0].get("count") or 0) if rows else 0)

    def _next_id(self) -> int:
        rows = self.pinot.query("SELECT MAX(idprospecto) AS max_id FROM Dim_Prospecto")
        return int((rows[0].get("max_id") or 0) if rows else 0) + 1
