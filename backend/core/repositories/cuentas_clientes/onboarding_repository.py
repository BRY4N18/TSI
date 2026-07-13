"""Onboarding repository — Fact_Onboarding read via Pinot, write via Kafka."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter


class OnboardingRepository:
    """Repository for Fact_Onboarding entity."""

    TOPIC = settings.KAFKA_TOPICS["onboarding"]

    def __init__(
        self,
        pinot: PinotClient | None = None,
        kafka: KafkaWriter | None = None,
    ):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def list_by_cliente(self, id_cliente: int) -> list[dict[str, Any]]:
        return self.pinot.query(
            """
            SELECT * FROM Fact_Onboarding
            WHERE id_cliente = %(id_cliente)s
            """,
            {"id_cliente": id_cliente},
        )

    def find_etapa(self, id_cliente: int, etapa: str) -> dict[str, Any] | None:
        rows = self.pinot.query(
            """
            SELECT * FROM Fact_Onboarding
            WHERE id_cliente = %(id_cliente)s AND etapa = %(etapa)s
            LIMIT 1
            """,
            {"id_cliente": id_cliente, "etapa": etapa},
        )
        return rows[0] if rows else None

    def complete_etapa(
        self,
        id_cliente: int,
        etapa: str,
        *,
        fecha_completado: int | None = None,
    ) -> dict[str, Any]:
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        completed_at = fecha_completado if fecha_completado is not None else now_ms
        now = datetime.now(timezone.utc).isoformat()
        existing = self.find_etapa(id_cliente, etapa)
        onboarding_id = existing["id_onboarding"] if existing else self._next_id()
        payload = {
            "id_onboarding": onboarding_id,
            "id_cliente": id_cliente,
            "etapa": etapa,
            "completado": True,
            "fecha_completado": completed_at,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def _next_id(self) -> int:
        rows = self.pinot.query("SELECT MAX(id_onboarding) AS max_id FROM Fact_Onboarding")
        max_id = rows[0].get("max_id") if rows else 0
        return int(max_id or 0) + 1
