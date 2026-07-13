"""Server access repository — CU-O15 entities."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter


class ServerAccessRepository:
    """Repository for server-level access entities (CU-O15)."""

    SERVER_USER_TOPIC = settings.KAFKA_TOPICS["server_user"]
    SERVER_ROLE_TOPIC = settings.KAFKA_TOPICS["server_role"]
    SERVER_USER_ROLE_TOPIC = settings.KAFKA_TOPICS["server_user_role"]
    SERVER_ROLE_MAPPING_TOPIC = settings.KAFKA_TOPICS["server_role_mapping"]

    def __init__(
        self,
        pinot: PinotClient | None = None,
        kafka: KafkaWriter | None = None,
    ):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    # --- Server users ---
    def list_server_users(self) -> list[dict[str, Any]]:
        return self.pinot.query("SELECT * FROM Dim_UsuariosServidor ORDER BY idusuariosservidor ASC")

    def find_server_user_by_id(self, server_user_id: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Dim_UsuariosServidor WHERE idusuariosservidor = %(id)s LIMIT 1",
            {"id": server_user_id},
        )
        return rows[0] if rows else None

    def create_server_user(self, data: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        server_user_id = self._next_server_user_id()
        payload = {
            "idusuariosservidor": server_user_id,
            "usuario": data["usuario"],
            "contrasena": data.get("contrasena", ""),
            "activo": data.get("activo", True),
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.SERVER_USER_TOPIC, payload)
        return payload

    def update_server_user(self, server_user_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        existing = self.find_server_user_by_id(server_user_id)
        if not existing:
            return None
        now = datetime.now(timezone.utc).isoformat()
        payload = {**existing, **data, "fecha_actualizacion": now}
        self.kafka.publish(self.SERVER_USER_TOPIC, payload)
        return payload

    # --- Server roles ---
    def list_server_roles(self) -> list[dict[str, Any]]:
        return self.pinot.query("SELECT * FROM Dim_RolesServidor ORDER BY idrolservidor ASC")

    def find_server_role_by_id(self, server_role_id: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Dim_RolesServidor WHERE idrolservidor = %(id)s LIMIT 1",
            {"id": server_role_id},
        )
        return rows[0] if rows else None

    def create_server_role(self, data: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        server_role_id = self._next_server_role_id()
        payload = {
            "idrolservidor": server_role_id,
            "rolservidor": data["rolservidor"],
            "descripcion": data.get("descripcion", ""),
            "activo": data.get("activo", True),
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.SERVER_ROLE_TOPIC, payload)
        return payload

    def update_server_role(self, server_role_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        existing = self.find_server_role_by_id(server_role_id)
        if not existing:
            return None
        now = datetime.now(timezone.utc).isoformat()
        payload = {**existing, **data, "fecha_actualizacion": now}
        self.kafka.publish(self.SERVER_ROLE_TOPIC, payload)
        return payload

    # --- Assignments ---
    def assign_server_role(
        self, server_user_id: int, server_role_id: int
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "idusuariosservidor": server_user_id,
            "idrolservidor": server_role_id,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.SERVER_USER_ROLE_TOPIC, payload)
        return payload

    def map_server_role_to_app_role(
        self, server_role_id: int, app_role_id: int
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "idrolservidor": server_role_id,
            "idrol": app_role_id,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.SERVER_ROLE_MAPPING_TOPIC, payload)
        return payload

    def get_server_user_roles(self, server_user_id: int) -> list[str]:
        links = self.pinot.query(
            "SELECT idrolservidor FROM Dim_UsuariosServidorRolesServidor WHERE idusuariosservidor = %(id)s",
            {"id": server_user_id},
        )
        role_ids = [row["idrolservidor"] for row in links]
        if not role_ids:
            return []
        roles = self.pinot.query(
            "SELECT rolservidor FROM Dim_RolesServidor WHERE idrolservidor IN %(role_ids)s",
            {"role_ids": role_ids},
        )
        return [row["rolservidor"] for row in roles]

    def _next_server_user_id(self) -> int:
        rows = self.pinot.query("SELECT MAX(idusuariosservidor) AS max_id FROM Dim_UsuariosServidor")
        max_id = rows[0].get("max_id") if rows else 0
        return (max_id or 0) + 1

    def _next_server_role_id(self) -> int:
        rows = self.pinot.query("SELECT MAX(idrolservidor) AS max_id FROM Dim_RolesServidor")
        max_id = rows[0].get("max_id") if rows else 0
        return (max_id or 0) + 1
