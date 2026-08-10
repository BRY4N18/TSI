"""Fact_CierreAccidente repository — Pinot read, Kafka write.

Extensión 1:1 de Fact_Accidente para los campos de cierre (RF-SEG-004):
`resultado_atencion`, `calificacion`, `observaciones_finales`. Separada de
Fact_Accidente porque esas columnas no existen en su esquema real
(corrección 2026-08-08 — antes se escribían ahí y se perdían en silencio).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.accidentes.kafka_writer import KafkaWriter


class CierreAccidenteRepository:
    TOPIC = settings.KAFKA_TOPICS["cierre_accidente"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def find_by_id(self, idaccidente: str) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Fact_CierreAccidente WHERE idaccidente = %(idaccidente)s LIMIT 1",
            {"idaccidente": idaccidente},
        )
        return rows[0] if rows else None

    def registrar(
        self,
        *,
        idaccidente: str,
        resultado_atencion: str,
        calificacion: int | None = None,
        observaciones_finales: str | None = None,
    ) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            "idaccidente": idaccidente,
            "resultado_atencion": resultado_atencion,
            "calificacion": calificacion,
            "observaciones_finales": observaciones_finales,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload
