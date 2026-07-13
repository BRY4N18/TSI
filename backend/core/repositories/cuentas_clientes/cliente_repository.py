"""Cliente repository — Dim_Cliente read via Pinot, write via Kafka."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter


class ClienteRepository:
    """Repository for Dim_Cliente entity."""

    TOPIC = settings.KAFKA_TOPICS["cliente"]

    def __init__(
        self,
        pinot: PinotClient | None = None,
        kafka: KafkaWriter | None = None,
    ):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def find_by_id(self, cliente_id: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Dim_Cliente WHERE idcliente = %(idcliente)s LIMIT 1",
            {"idcliente": cliente_id},
        )
        return rows[0] if rows else None

    def find_by_nit(self, nit: str) -> dict[str, Any] | None:
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_Cliente
            WHERE nit_identificacion = %(nit)s LIMIT 1
            """,
            {"nit": nit},
        )
        return rows[0] if rows else None

    def find_by_admin_local(self, user_id: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_Cliente
            WHERE admin_local_id = %(admin_local_id)s LIMIT 1
            """,
            {"admin_local_id": user_id},
        )
        return rows[0] if rows else None

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        cliente_id = self._next_id()
        payload = {
            "idcliente": cliente_id,
            "razon_social": data["razon_social"],
            "nombre": data.get("nombre", ""),
            "tipo": data["tipo"],
            "nit_identificacion": data["nit_identificacion"],
            "fecha_inicio_contrato": data.get("fecha_inicio_contrato"),
            "plan_suscripcion": data.get("plan_suscripcion"),
            "logo_url": data.get("logo_url"),
            "estado_onboarding": data.get("estado_onboarding"),
            "estado": data.get("estado", "Activo"),
            "admin_local_id": data["admin_local_id"],
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def update(self, cliente_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        existing = self.find_by_id(cliente_id)
        if not existing:
            return None
        now = datetime.now(timezone.utc).isoformat()
        payload = {**existing, **data, "fecha_actualizacion": now}
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def _next_id(self) -> int:
        rows = self.pinot.query("SELECT MAX(idcliente) AS max_id FROM Dim_Cliente")
        max_id = rows[0].get("max_id") if rows else 0
        return int(max_id or 0) + 1
