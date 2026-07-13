"""Dim_ElementoFisicoAccidente repository."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.repositories.accidentes.kafka_writer import KafkaWriter


class ElementoFisicoRepository:
    TOPIC = settings.KAFKA_TOPICS["elemento_fisico_accidente"]

    def __init__(self, kafka: KafkaWriter | None = None):
        self.kafka = kafka or KafkaWriter()

    def upsert(self, *, idaccidente: str, idelementofisico: int, idusuario: int) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            "idelementosfisicosaccidente": hash((idaccidente, idelementofisico)) % 1_000_000,
            "idaccidente": idaccidente,
            "idelementofisico": idelementofisico,
            "idusuario": idusuario,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload
