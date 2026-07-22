"""Dim_ValidacionRegion write repository — historial append-only (CU-O55/O60).

Forma esperada de cada fila (dict[str, Any], sin dataclass — mismo patrón que
unidad_emergencia_repository.py):
    idvalidacionregion: int
    idregionoperativa: int
    idusuario: int
    resultado: str            # 'Aprobada' | 'Rechazada' (STRING libre, RN-REGON-002)
    motivo: str | None        # obligatorio solo si resultado == 'Rechazada'
    fechahora: str            # ISO-8601
    fecha_actualizacion: str  # ISO-8601
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.red_operativa.kafka_writer import KafkaWriter

RESULTADO_APROBADA = "Aprobada"
RESULTADO_RECHAZADA = "Rechazada"


class ValidacionRegionRepository:
    """Repository for Dim_ValidacionRegion — nunca sobrescribe, solo inserta (RNF-REGON-001)."""

    TOPIC = settings.KAFKA_TOPICS["validacion_region_snapshot"]

    def __init__(
        self,
        pinot: PinotClient | None = None,
        kafka: KafkaWriter | None = None,
    ):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "idvalidacionregion": self._next_id(),
            "idregionoperativa": data["idregionoperativa"],
            "idusuario": data["idusuario"],
            "resultado": data["resultado"],
            "motivo": data.get("motivo"),
            "fechahora": data.get("fechahora", now),
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def list_by_region(self, idregionoperativa: int) -> list[dict[str, Any]]:
        rows = self.pinot.query(
            "SELECT * FROM Dim_ValidacionRegion WHERE idregionoperativa = %(idregionoperativa)s",
            {"idregionoperativa": idregionoperativa},
        )
        return sorted(rows, key=lambda r: r["fechahora"])

    def existe_aprobada(self, idregionoperativa: int) -> bool:
        return any(
            r["resultado"] == RESULTADO_APROBADA for r in self.list_by_region(idregionoperativa)
        )

    def _next_id(self) -> int:
        rows = self.pinot.query(
            "SELECT MAX(idvalidacionregion) AS max_id FROM Dim_ValidacionRegion"
        )
        max_id = rows[0].get("max_id") if rows else 0
        return int(max_id or 0) + 1
