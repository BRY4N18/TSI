"""Role repository — Dim_Rol and Dim_Usuario_Rol."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter


class RoleRepository:
    """Repository for Dim_Rol and Dim_Usuario_Rol entities."""

    ROLE_TOPIC = settings.KAFKA_TOPICS["role"]
    USER_ROLE_TOPIC = settings.KAFKA_TOPICS["user_role"]

    def __init__(
        self,
        pinot: PinotClient | None = None,
        kafka: KafkaWriter | None = None,
    ):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def find_role_by_id(self, role_id: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Dim_Rol WHERE idrol = %(idrol)s LIMIT 1",
            {"idrol": role_id},
        )
        return rows[0] if rows else None

    def find_role_by_name(self, rol: str) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Dim_Rol WHERE rol = %(rol)s LIMIT 1",
            {"rol": rol},
        )
        return rows[0] if rows else None

    def list_roles(self) -> list[dict[str, Any]]:
        return self.pinot.query("SELECT * FROM Dim_Rol ORDER BY idrol ASC")

    def create_role(self, data: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        role_id = self._next_role_id()
        payload = {
            "idrol": role_id,
            "rol": data["rol"],
            "descripcion": data.get("descripcion", ""),
            "activo": data.get("activo", True),
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.ROLE_TOPIC, payload)
        return payload

    def update_role(self, role_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        existing = self.find_role_by_id(role_id)
        if not existing:
            return None
        now = datetime.now(timezone.utc).isoformat()
        payload = {**existing, **data, "fecha_actualizacion": now}
        self.kafka.publish(self.ROLE_TOPIC, payload)
        return payload

    def deactivate_role(self, role_id: int) -> dict[str, Any] | None:
        return self.update_role(role_id, {"activo": False})

    def get_user_roles(self, user_id: int) -> list[str]:
        links = self.pinot.query(
            "SELECT idrol FROM Dim_Usuario_Rol WHERE idusuario = %(idusuario)s",
            {"idusuario": user_id},
        )
        role_ids = [row["idrol"] for row in links]
        if not role_ids:
            return []
        roles = self.pinot.query(
            "SELECT rol FROM Dim_Rol WHERE idrol IN %(role_ids)s AND activo = true",
            {"role_ids": role_ids},
        )
        return [row["rol"] for row in roles]

    def assign_role_to_user(self, user_id: int, role_id: int) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "idusuario": user_id,
            "idrol": role_id,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.USER_ROLE_TOPIC, payload)
        return payload

    def _next_role_id(self) -> int:
        rows = self.pinot.query("SELECT MAX(idrol) AS max_id FROM Dim_Rol")
        max_id = rows[0].get("max_id") if rows else 0
        return (max_id or 0) + 1
