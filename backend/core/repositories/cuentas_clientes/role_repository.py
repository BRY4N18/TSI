"""Role repository — Dim_Rol and Dim_Usuario_Rol."""

from __future__ import annotations

from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.pinot.tiempo import ahora_ms
from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter
from core.pinot.secuencia import siguiente_id


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
        now = ahora_ms()
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
        now = ahora_ms()
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

    def list_user_ids_for_role(self, rol: str) -> list[int]:
        """Return user ids assigned to an active role name (Dim_Usuario_Rol)."""
        role = self.find_role_by_name(rol)
        if not role or not role.get("activo", True):
            return []
        links = self.pinot.query(
            "SELECT idusuario FROM Dim_Usuario_Rol WHERE idrol = %(idrol)s",
            {"idrol": int(role["idrol"])},
        )
        return [int(row["idusuario"]) for row in links]

    def assign_role_to_user(self, user_id: int, role_id: int) -> dict[str, Any]:
        """Asigna un rol, generando la clave primaria de `Dim_Usuario_Rol`.

        El payload no llevaba `idusuariorol`. Como Pinot no almacena NULL, la fila
        aterrizaba con el defecto para INT (`Integer.MIN_VALUE`) y, al ser una tabla
        upsert por esa clave, **cada asignación nueva sobrescribía a la anterior**:
        solo podía existir una en todo el sistema. El usuario pisado se quedaba sin
        roles y su login pasaba a fallar con "Usuario sin roles asignados".
        """
        existente = self.find_user_role(user_id, role_id)
        if existente:
            return existente
        now = ahora_ms()
        payload = {
            "idusuariorol": self._next_user_role_id(),
            "idusuario": user_id,
            "idrol": role_id,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.USER_ROLE_TOPIC, payload)
        return payload

    def find_user_role(self, user_id: int, role_id: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Dim_Usuario_Rol WHERE idusuario = %(idusuario)s "
            "AND idrol = %(idrol)s LIMIT 1",
            {"idusuario": int(user_id), "idrol": int(role_id)},
        )
        return rows[0] if rows else None

    def _next_user_role_id(self) -> int:
        # Las filas huérfanas que quedaron con Integer.MIN_VALUE no deben
        # arrastrar el contador a negativo. `siguiente_id` ya lo garantiza: parte
        # de `max(maximo, entregado)` con `entregado` a 0 como mínimo.
        return siguiente_id(self.pinot, "Dim_Usuario_Rol", "idusuariorol")

    def _next_role_id(self) -> int:
        return siguiente_id(self.pinot, "Dim_Rol", "idrol")
