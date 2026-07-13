"""Credential repository — Dim_Credencial."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import bcrypt
from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter


class CredentialRepository:
    """Repository for Dim_Credencial entity."""

    TOPIC = settings.KAFKA_TOPICS["credential"]
    BCRYPT_ROUNDS = 12

    def __init__(
        self,
        pinot: PinotClient | None = None,
        kafka: KafkaWriter | None = None,
    ):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def find_by_user_id(self, user_id: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Dim_Credencial WHERE idusuario = %(idusuario)s LIMIT 1",
            {"idusuario": user_id},
        )
        return rows[0] if rows else None

    def verify_password(self, plain_password: str, hashed: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed.encode("utf-8"),
        )

    def hash_password(self, plain_password: str) -> str:
        return bcrypt.hashpw(
            plain_password.encode("utf-8"),
            bcrypt.gensalt(rounds=self.BCRYPT_ROUNDS),
        ).decode("utf-8")

    def create_temporary(self, user_id: int, temp_password: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        cred_id = self._next_id()
        payload = {
            "idcredencial": cred_id,
            "idusuario": user_id,
            "contrasena": self.hash_password(temp_password),
            "estadocredencial": "Cambio contraseña",
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def create(self, user_id: int, plain_password: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        cred_id = self._next_id()
        payload = {
            "idcredencial": cred_id,
            "idusuario": user_id,
            "contrasena": self.hash_password(plain_password),
            "estadocredencial": "Activo",
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def reset_password(self, user_id: int, temporary_password: str) -> dict[str, Any] | None:
        existing = self.find_by_user_id(user_id)
        if not existing:
            return None
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            **existing,
            "contrasena": self.hash_password(temporary_password),
            "estadocredencial": "Cambio contraseña",
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def activate_credential(self, user_id: int, new_password: str) -> dict[str, Any] | None:
        existing = self.find_by_user_id(user_id)
        if not existing:
            return None
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            **existing,
            "contrasena": self.hash_password(new_password),
            "estadocredencial": "Activo",
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def _next_id(self) -> int:
        rows = self.pinot.query("SELECT MAX(idcredencial) AS max_id FROM Dim_Credencial")
        max_id = rows[0].get("max_id") if rows else 0
        return int(max_id or 0) + 1
