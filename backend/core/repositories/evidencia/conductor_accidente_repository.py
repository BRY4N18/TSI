"""Fact_Conductor_Accidente repository — Pinot read, Kafka write."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.accidentes.kafka_writer import KafkaWriter


class ConductorAccidenteRepository:
    TOPIC = settings.KAFKA_TOPICS["conductor_accidente"]

    def __init__(
        self,
        pinot: PinotClient | None = None,
        kafka: KafkaWriter | None = None,
    ):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _next_id(self) -> int:
        rows = self.pinot.query(
            "SELECT MAX(idconductoraccidente) AS max_id FROM Fact_Conductor_Accidente",
            {},
        )
        return int(rows[0]["max_id"] or 0) + 1 if rows else 1

    def list_activos_by_accidente(self, idaccidente: str) -> list[dict[str, Any]]:
        rows = self.pinot.query(
            """
            SELECT * FROM Fact_Conductor_Accidente
            WHERE idaccidente = %(idaccidente)s
            """,
            {"idaccidente": idaccidente},
        )
        return [r for r in rows if r.get("activo", True)]

    def find_by_id(self, idconductoraccidente: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            """
            SELECT * FROM Fact_Conductor_Accidente
            WHERE idconductoraccidente = %(id)s
            LIMIT 1
            """,
            {"id": idconductoraccidente},
        )
        return rows[0] if rows else None

    def create(
        self,
        *,
        idaccidente: str,
        idconductor: int,
        idestadoconductor: int,
        idvehiculo: int,
        idusuario: int,
    ) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            "idconductoraccidente": self._next_id(),
            "idaccidente": idaccidente,
            "idconductor": idconductor,
            "idestadoconductor": idestadoconductor,
            "idvehiculo": idvehiculo,
            "idusuario": idusuario,
            "activo": True,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def soft_delete(
        self, *, idconductoraccidente: int, idusuario: int
    ) -> dict[str, Any] | None:
        current = self.find_by_id(idconductoraccidente)
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
