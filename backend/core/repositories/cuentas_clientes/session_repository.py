"""Session repository — Fact_Session read via Pinot, write via Kafka."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter


class SessionRepository:
    """Repository for Fact_Session entity."""

    TOPIC = settings.KAFKA_TOPICS["session"]

    def __init__(
        self,
        pinot: PinotClient | None = None,
        kafka: KafkaWriter | None = None,
    ):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def find_by_id(self, session_id: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Fact_Session WHERE idsession = %(idsession)s LIMIT 1",
            {"idsession": session_id},
        )
        return rows[0] if rows else None

    def find_active_by_user(self, user_id: int) -> list[dict[str, Any]]:
        return self.pinot.query(
            """
            SELECT * FROM Fact_Session
            WHERE idusuario = %(idusuario)s AND estadosession = 'Inicio sesion'
            """,
            {"idusuario": user_id},
        )

    def create(
        self,
        *,
        user_id: int,
        token: str,
        navegador: str,
        refresh_token: str,
    ) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        session_id = self._next_id()
        payload = {
            "idsession": session_id,
            "idusuario": user_id,
            "token": token,
            "refresh_token": refresh_token,
            "navegador": navegador,
            "fechahorainiciosesion": now,
            "fechahoracierresesion": None,
            "estadosession": "Inicio sesion",
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def close_session(self, session_id: int) -> dict[str, Any] | None:
        session = self.find_by_id(session_id)
        if not session:
            return None
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            **session,
            "estadosession": "Cierre sesion",
            "fechahoracierresesion": now,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def revoke_session(self, session_id: int) -> dict[str, Any] | None:
        session = self.find_by_id(session_id)
        if not session:
            return None
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            **session,
            "estadosession": "Expulsado",
            "fechahoracierresesion": now,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def is_active(self, session_id: int) -> bool:
        session = self.find_by_id(session_id)
        if not session:
            return False
        return session.get("estadosession") == "Inicio sesion"

    def expel_all_by_cliente(self, cliente_id: int) -> int:
        """Expel all active sessions for users belonging to cliente (CU-O11)."""
        from core.repositories.cuentas_clientes.cuenta_usuario_repository import (
            CuentaUsuarioRepository,
        )

        cuenta_usuario_repo = CuentaUsuarioRepository(pinot=self.pinot)
        users = cuenta_usuario_repo.list_active_by_cliente(cliente_id)
        count = 0
        for user in users:
            sessions = self.find_active_by_user(user["idusuario"])
            for session in sessions:
                self.revoke_session(session["idsession"])
                count += 1
        return count

    def _next_id(self) -> int:
        rows = self.pinot.query("SELECT MAX(idsession) AS max_id FROM Fact_Session")
        max_id = rows[0].get("max_id") if rows else 0
        return int(max_id or 0) + 1
