"""Dim_NotaAccidente repository."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.repositories.accidentes.kafka_writer import KafkaWriter


class NotaAccidenteRepository:
    TOPIC = settings.KAFKA_TOPICS["nota_accidente"]

    def __init__(self, kafka: KafkaWriter | None = None):
        self.kafka = kafka or KafkaWriter()

    def create_escalamiento(
        self,
        *,
        idaccidente: str,
        idusuario: int,
        nota: str,
    ) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            "idnotaaccidentes": hash((idaccidente, now)) % 1_000_000,
            "idaccidente": idaccidente,
            "idusuario": idusuario,
            "nota": nota,
            "tipo": "escalamiento",
            "sincronizado": True,
            "activo": True,
            "fechahora": now,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def create_motivo(
        self,
        *,
        idaccidente: str,
        idusuario: int,
        nota: str,
    ) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            "idnotaaccidentes": hash((idaccidente, now, "motivo")) % 1_000_000,
            "idaccidente": idaccidente,
            "idusuario": idusuario,
            "nota": nota,
            "tipo": "motivo",
            "sincronizado": True,
            "activo": True,
            "fechahora": now,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def create_alerta(
        self,
        *,
        idaccidente: str,
        idusuario: int,
        nota: str,
    ) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            "idnotaaccidentes": hash((idaccidente, now, "alerta")) % 1_000_000,
            "idaccidente": idaccidente,
            "idusuario": idusuario,
            "nota": nota,
            "tipo": "alerta",
            "sincronizado": True,
            "activo": True,
            "fechahora": now,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload
