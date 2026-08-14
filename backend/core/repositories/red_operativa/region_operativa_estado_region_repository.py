"""Dim_RegionOperativaEstadoRegion — puente geográfico región ↔ Dim_EstadoRegion.

Escrito en alta de región (CU-O55) para que Emergencias pueda resolver cobertura.
No es historial de ciclo de vida (eso vive en Dim_RegionOperativa.estadoregion).
"""

from __future__ import annotations

from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.pinot.tiempo import ahora_ms
from core.repositories.red_operativa.kafka_writer import KafkaWriter


class RegionOperativaEstadoRegionRepository:
    TOPIC = settings.KAFKA_TOPICS["region_operativa_estado_region"]

    def __init__(
        self,
        pinot: PinotClient | None = None,
        kafka: KafkaWriter | None = None,
    ):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def list_by_region(self, idregionoperativa: int) -> list[dict[str, Any]]:
        return self.pinot.query(
            "SELECT * FROM Dim_RegionOperativaEstadoRegion "
            "WHERE idregionoperativa = %(idregionoperativa)s",
            {"idregionoperativa": idregionoperativa},
        )

    def ensure_link(
        self,
        *,
        idregionoperativa: int,
        idestadoregion: int,
        nombreregion: str | None = None,
    ) -> dict[str, Any]:
        existing = [
            r
            for r in self.list_by_region(idregionoperativa)
            if int(r.get("idestadoregion", -1)) == int(idestadoregion)
        ]
        if existing:
            return existing[0]

        now = ahora_ms()
        payload = {
            "idregionoperativaestadoregion": self._next_id(),
            "idregionoperativa": idregionoperativa,
            "idestadoregion": idestadoregion,
            "nombreregion": nombreregion or "",
            "activo": True,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def _next_id(self) -> int:
        rows = self.pinot.query(
            "SELECT MAX(idregionoperativaestadoregion) AS max_id "
            "FROM Dim_RegionOperativaEstadoRegion"
        )
        max_id = rows[0].get("max_id") if rows else 0
        return int(max_id or 0) + 1
