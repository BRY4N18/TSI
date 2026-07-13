"""User repository — Dim_Usuarios read via Pinot, write via Kafka."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter


class UserRepository:
    """Repository for Dim_Usuarios entity."""

    TOPIC = settings.KAFKA_TOPICS["user"]

    def __init__(
        self,
        pinot: PinotClient | None = None,
        kafka: KafkaWriter | None = None,
    ):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def find_by_id(self, user_id: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Dim_Usuarios WHERE idusuario = %(idusuario)s LIMIT 1",
            {"idusuario": user_id},
        )
        return rows[0] if rows else None

    def find_by_gmail(self, gmail: str) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Dim_Usuarios WHERE gmail = %(gmail)s LIMIT 1",
            {"gmail": gmail},
        )
        return rows[0] if rows else None

    def list_users(self, *, cursor: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        sql = "SELECT * FROM Dim_Usuarios ORDER BY idusuario ASC LIMIT %(limit)s"
        params: dict[str, Any] = {"limit": limit}
        if cursor:
            sql = (
                "SELECT * FROM Dim_Usuarios WHERE idusuario > %(cursor)s "
                "ORDER BY idusuario ASC LIMIT %(limit)s"
            )
            params["cursor"] = int(cursor)
        return self.pinot.query(sql, params)

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        user_id = self._next_id()
        payload = {
            "idusuario": user_id,
            "nombres": data["nombres"],
            "apellidos": data["apellidos"],
            "gmail": data["gmail"],
            "identificacion": data.get("identificacion", ""),
            "genero": data.get("genero", ""),
            "telefono": data.get("telefono", ""),
            "fechanacimiento": data.get("fechanacimiento", ""),
            "activo": data.get("activo", True),
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def update(self, user_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        existing = self.find_by_id(user_id)
        if not existing:
            return None
        now = datetime.now(timezone.utc).isoformat()
        payload = {**existing, **data, "fecha_actualizacion": now}
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def deactivate(self, user_id: int) -> dict[str, Any] | None:
        return self.update(user_id, {"activo": False})

    def _next_id(self) -> int:
        rows = self.pinot.query("SELECT MAX(idusuario) AS max_id FROM Dim_Usuarios")
        max_id = rows[0].get("max_id") if rows else 0
        return int(max_id or 0) + 1
