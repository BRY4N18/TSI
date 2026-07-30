"""Dim_ElementoClimaticosAccidente repository — Pinot read, Kafka write."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.accidentes.kafka_writer import KafkaWriter


class ElementoClimaticoRepository:
    TOPIC = settings.KAFKA_TOPICS["elemento_climatico_accidente"]

    def __init__(
        self,
        pinot: PinotClient | None = None,
        kafka: KafkaWriter | None = None,
    ):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def find_activo_by_accidente(self, idaccidente: str) -> dict[str, Any] | None:
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_ElementoClimaticosAccidente
            WHERE idaccidente = %(idaccidente)s
            """,
            {"idaccidente": idaccidente},
        )
        activos = [r for r in rows if r.get("activo", True)]
        if not activos:
            return None
        activos.sort(key=lambda r: r.get("fecha_actualizacion", 0), reverse=True)
        return activos[0]

    def upsert(
        self,
        *,
        idaccidente: str,
        idperiododia: int | None,
        idestadoclima: int | None,
        idusuario: int,
    ) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        existing = self.find_activo_by_accidente(idaccidente)
        if existing:
            superseded = {**existing, "activo": False, "fecha_actualizacion": now}
            self.kafka.publish(self.TOPIC, superseded)
        payload = {
            "idelementoclimaticoaccidente": (hash((idaccidente, now)) % 1_000_000) or 1,
            "idaccidente": idaccidente,
            "idperiododia": idperiododia,
            "idestadoclima": idestadoclima,
            "idusuario": idusuario,
            "activo": True,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload
