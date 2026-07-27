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
        """NIT activo para duplicados — excluye soft-anulados (Rechazado_Anulado)."""
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_Cliente
            WHERE nit_identificacion = %(nit)s
              AND estado <> 'Rechazado_Anulado'
            LIMIT 1
            """,
            {"nit": nit},
        )
        return rows[0] if rows else None

    def exists_by_nit_any(self, nit: str) -> bool:
        """Return whether a NIT exists regardless of the client's state."""
        rows = self.pinot.query(
            "SELECT idcliente FROM Dim_Cliente WHERE nit_identificacion = %(nit)s LIMIT 1",
            {"nit": nit},
        )
        return bool(rows)

    def find_by_admin_local(self, user_id: int) -> dict[str, Any] | None:
        """Cuenta vigente del admin local — excluye soft-anulados."""
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_Cliente
            WHERE admin_local_id = %(admin_local_id)s
              AND estado <> 'Rechazado_Anulado'
            LIMIT 1
            """,
            {"admin_local_id": user_id},
        )
        return rows[0] if rows else None

    def list_by_estado(self, estado: str) -> list[dict[str, Any]]:
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_Cliente
            WHERE estado = %(estado)s
            """,
            {"estado": estado},
        )
        return list(rows or [])

    def update_estado(
        self,
        cliente_id: int,
        *,
        estado: str,
        estado_onboarding: str | None = None,
    ) -> dict[str, Any] | None:
        data: dict[str, Any] = {"estado": estado}
        if estado_onboarding is not None:
            data["estado_onboarding"] = estado_onboarding
        return self.update(cliente_id, data)

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
            "idprospecto": data.get("idprospecto"),
            "admin_local_id": data.get("admin_local_id"),
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
