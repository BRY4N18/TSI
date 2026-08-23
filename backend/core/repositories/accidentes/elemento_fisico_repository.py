"""Dim_ElementoFisicoAccidente repository — Pinot read, Kafka write."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.accidentes.kafka_writer import KafkaWriter
from core.pinot.secuencia import siguiente_id


class ElementoFisicoRepository:
    TOPIC = settings.KAFKA_TOPICS["elemento_fisico_accidente"]

    def __init__(
        self,
        pinot: PinotClient | None = None,
        kafka: KafkaWriter | None = None,
    ):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _next_id(self) -> int:
        return siguiente_id(self.pinot, "Dim_ElementoFisicoAccidente", "idelementosfisicosaccidente")

    def list_activos_by_accidente(self, idaccidente: str) -> list[dict[str, Any]]:
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_ElementoFisicoAccidente
            WHERE idaccidente = %(idaccidente)s
            """,
            {"idaccidente": idaccidente},
        )
        return [r for r in rows if r.get("activo", True)]

    def find_by_id(self, idelementosfisicosaccidente: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_ElementoFisicoAccidente
            WHERE idelementosfisicosaccidente = %(id)s
            LIMIT 1
            """,
            {"id": idelementosfisicosaccidente},
        )
        return rows[0] if rows else None

    def upsert(self, *, idaccidente: str, idelementofisico: int, idusuario: int) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        activos = self.list_activos_by_accidente(idaccidente)
        existing = next(
            (r for r in activos if r.get("idelementofisico") == idelementofisico),
            None,
        )
        payload = {
            "idelementosfisicosaccidente": (
                existing["idelementosfisicosaccidente"] if existing else self._next_id()
            ),
            "idaccidente": idaccidente,
            "idelementofisico": idelementofisico,
            "idusuario": idusuario,
            "activo": True,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def soft_delete(
        self, *, idelementosfisicosaccidente: int, idusuario: int
    ) -> dict[str, Any] | None:
        current = self.find_by_id(idelementosfisicosaccidente)
        if not current:
            return None
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            **current,
            "activo": False,
            "idusuario": idusuario,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload
