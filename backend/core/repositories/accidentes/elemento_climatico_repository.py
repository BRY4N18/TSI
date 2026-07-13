"""Dim_ElementoClimaticosAccidente repository."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.repositories.accidentes.kafka_writer import KafkaWriter


class ElementoClimaticoRepository:
    TOPIC = settings.KAFKA_TOPICS["elemento_climatico_accidente"]

    def __init__(self, kafka: KafkaWriter | None = None):
        self.kafka = kafka or KafkaWriter()

    def upsert(
        self,
        *,
        idaccidente: str,
        idperiododia: int | None,
        idestadoclima: int | None,
        idusuario: int,
    ) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            "idelementoclimaticoaccidente": hash(idaccidente) % 1_000_000,
            "idaccidente": idaccidente,
            "idperiododia": idperiododia,
            "idestadoclima": idestadoclima,
            "idusuario": idusuario,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload
