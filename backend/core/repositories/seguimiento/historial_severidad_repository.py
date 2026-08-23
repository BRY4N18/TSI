"""Fact_HistorialSeveridadAccidente repository — Pinot read, Kafka write.

RF-O73.2: conserva la severidad inicial junto a la escalada, sin sobrescribirla.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.accidentes.kafka_writer import KafkaWriter
from core.pinot.secuencia import siguiente_id


class HistorialSeveridadRepository:
    TOPIC = settings.KAFKA_TOPICS["historial_severidad_accidente"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _next_id(self) -> int:
        return siguiente_id(self.pinot, "Fact_HistorialSeveridadAccidente", "idhistorialseveridadaccidente")

    def list_by_accidente(self, idaccidente: str) -> list[dict[str, Any]]:
        rows = self.pinot.query(
            """
            SELECT * FROM Fact_HistorialSeveridadAccidente
            WHERE idaccidente = %(idaccidente)s
            """,
            {"idaccidente": idaccidente},
        )
        rows.sort(key=lambda r: r.get("fechahora", 0))
        return rows

    def registrar_escalada(
        self,
        *,
        idaccidente: str,
        idseveridadanterior: int,
        idseveridadnueva: int,
        idusuario: int,
        motivo: str | None = None,
    ) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            "idhistorialseveridadaccidente": self._next_id(),
            "idaccidente": idaccidente,
            "idseveridadanterior": idseveridadanterior,
            "idseveridadnueva": idseveridadnueva,
            "idusuario": idusuario,
            "motivo": motivo,
            "fechahora": now,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload
