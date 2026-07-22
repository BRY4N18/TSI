"""Dim_RegionOperativa write repository — protocolo de onboarding (CU-O55/O60/O61/O62).

Forma esperada de cada fila (dict[str, Any], sin dataclass — mismo patrón que
unidad_emergencia_repository.py):
    idregionoperativa: int
    idestado: int            # FK a Dim_EstadoRegion
    nombreregion: str
    estadoregion: str        # 'En_Validación' | 'Producción' | 'En_Alerta' | 'Despublicada'
    activo: bool
    fecha_actualizacion: str # ISO-8601
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.red_operativa.kafka_writer import KafkaWriter

ESTADO_EN_VALIDACION = "En_Validación"


class RegionOperativaRepository:
    """Repository for Dim_RegionOperativa entity (escritura administrativa)."""

    TOPIC = settings.KAFKA_TOPICS["region_operativa_snapshot"]

    def __init__(
        self,
        pinot: PinotClient | None = None,
        kafka: KafkaWriter | None = None,
    ):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def find_by_id(self, idregionoperativa: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Dim_RegionOperativa WHERE idregionoperativa = %(idregionoperativa)s LIMIT 1",
            {"idregionoperativa": idregionoperativa},
        )
        return rows[0] if rows else None

    def list(
        self,
        *,
        cursor: int = 0,
        limit: int = 20,
        estadoregion: str | None = None,
    ) -> list[dict[str, Any]]:
        rows = self.pinot.query(
            "SELECT * FROM Dim_RegionOperativa WHERE idregionoperativa > %(cursor)s",
            {"cursor": cursor},
        )
        if estadoregion:
            rows = [r for r in rows if r.get("estadoregion") == estadoregion]
        return sorted(rows, key=lambda r: r["idregionoperativa"])[:limit]

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "idregionoperativa": self._next_id(),
            "idestado": data["idestado"],
            "nombreregion": data["nombreregion"],
            "estadoregion": data.get("estadoregion", ESTADO_EN_VALIDACION),
            "activo": data.get("activo", True),
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def update(self, idregionoperativa: int, data: dict[str, Any]) -> dict[str, Any] | None:
        existing = self.find_by_id(idregionoperativa)
        if not existing:
            return None
        now = datetime.now(timezone.utc).isoformat()
        payload = {**existing, **data, "fecha_actualizacion": now}
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def _next_id(self) -> int:
        rows = self.pinot.query("SELECT MAX(idregionoperativa) AS max_id FROM Dim_RegionOperativa")
        max_id = rows[0].get("max_id") if rows else 0
        return int(max_id or 0) + 1
