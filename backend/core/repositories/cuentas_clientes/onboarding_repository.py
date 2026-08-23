"""Onboarding repository — Fact_Onboarding read via Pinot, write via Kafka."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.pinot.tiempo import ahora_ms
from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter
from core.pinot.secuencia import siguiente_id


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
        now = ahora_ms()
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

    def iniciar_etapas(self, id_cliente: int, etapas: list[str]) -> list[dict[str, Any]]:
        """Deja constancia de las etapas que el cliente **tiene que** recorrer.

        ⚠️ **El abandono es una ausencia, y hasta ahora no había de qué ausentarse**
        (decisión #45). `Fact_Onboarding` solo recibía filas `completado = True`,
        así que un embudo calculado sobre lo observado daba **100 % de
        finalización**: las etapas que nadie hizo no existían.

        Al arrancar el onboarding se escriben las tres con `completado = False`.
        A partir de ahí, una etapa que sigue en `False` **es** el abandono
        observado — sin inventar un umbral de inactividad, que era lo que
        convertía esto en una decisión de negocio.

        Idempotente: una etapa que ya tiene fila —completada o no— no se toca.
        Reescribirla borraría una finalización real.
        """
        creadas = []
        for etapa in etapas:
            if self.find_etapa(id_cliente, etapa):
                continue
            payload = {
                "id_onboarding": self._next_id(),
                "id_cliente": id_cliente,
                "etapa": etapa,
                "completado": False,
                # ⚠️ Sin fecha: no se ha completado. El centinela de Pinot lo
                # dirá, y el modelo ya trata el 0 como ausencia.
                "fecha_completado": None,
                "fecha_actualizacion": ahora_ms(),
            }
            self.kafka.publish(self.TOPIC, payload)
            creadas.append(payload)
        return creadas

    def _next_id(self) -> int:
        return siguiente_id(self.pinot, "Fact_Onboarding", "id_onboarding")
