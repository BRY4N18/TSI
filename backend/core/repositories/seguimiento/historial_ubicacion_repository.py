"""Dim_HistorialUbicacionUnidadEmergencia — Pinot read, Kafka write."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.accidentes.kafka_writer import KafkaWriter


class HistorialUbicacionRepository:
    TOPIC = settings.KAFKA_TOPICS["historial_ubicacion_unidad"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _next_id(self) -> int:
        rows = self.pinot.query(
            """
            SELECT MAX(idhistorialubicacion) AS max_id
            FROM Dim_HistorialUbicacionUnidadEmergencia
            """,
            {},
        )
        return int(rows[0]["max_id"] or 0) + 1 if rows else 1

    def publish(
        self,
        *,
        idunidademergencia: int,
        idaccidente: str,
        latitud: float,
        longitud: float,
        fechahora: int | None = None,
    ) -> dict[str, Any]:
        now = fechahora or int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            "idhistorialubicacion": self._next_id(),
            "idunidademergencia": idunidademergencia,
            "idaccidente": idaccidente,
            "latitud": latitud,
            "longitud": longitud,
            "fechahora": now,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def list_by_unidad(self, idunidademergencia: int) -> list[dict[str, Any]]:
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_HistorialUbicacionUnidadEmergencia
            WHERE idunidademergencia = %(idunidademergencia)s
            """,
            {"idunidademergencia": idunidademergencia},
        )
        rows.sort(key=lambda r: r.get("fechahora", 0))
        return rows

    def latest_fechahora(self, idunidademergencia: int) -> int | None:
        rows = self.pinot.query(
            """
            SELECT fechahora FROM Dim_HistorialUbicacionUnidadEmergencia
            WHERE idunidademergencia = %(idunidademergencia)s
            ORDER BY fechahora DESC
            LIMIT 1
            """,
            {"idunidademergencia": idunidademergencia},
        )
        if not rows:
            return None
        return int(rows[0]["fechahora"])
