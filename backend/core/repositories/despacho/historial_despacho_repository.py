"""Fact_HistorialDespachoUnidad repository — append-only Kafka writes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.accidentes.kafka_writer import KafkaWriter

ESTADO_PENDIENTE = "Pendiente"
ESTADO_CONFIRMADO = "Confirmado"
ESTADO_RECHAZADO = "Rechazado"
ESTADO_TIMEOUT = "Timeout"
ESTADO_ABORTADO = "Abortado"
ESTADO_EN_SITIO = "En_sitio"
ESTADO_RETIRADO = "Retirado"
ESTADO_DEFAULT = ESTADO_PENDIENTE

ESTADO_ID_MAP = {
    ESTADO_PENDIENTE: 1,
    ESTADO_CONFIRMADO: 2,
    ESTADO_RECHAZADO: 3,
    ESTADO_TIMEOUT: 4,
    ESTADO_ABORTADO: 5,
    ESTADO_EN_SITIO: 6,
    ESTADO_RETIRADO: 7,
}


class HistorialDespachoRepository:
    TOPIC = settings.KAFKA_TOPICS["historial_despacho"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _next_id(self) -> int:
        rows = self.pinot.query(
            """
            SELECT MAX(idhistorialdespachounidad) AS max_id
            FROM Fact_HistorialDespachoUnidad
            """,
            {},
        )
        return int(rows[0]["max_id"] or 0) + 1 if rows else 1

    def list_by_despacho(self, iddespacho: int) -> list[dict[str, Any]]:
        rows = self.pinot.query(
            """
            SELECT * FROM Fact_HistorialDespachoUnidad
            WHERE iddespacho = %(iddespacho)s
            """,
            {"iddespacho": iddespacho},
        )
        rows.sort(key=lambda r: (r.get("fechahora", 0), r.get("idhistorialdespachounidad", 0)))
        return rows

    def get_current_estado(self, iddespacho: int) -> tuple[str, int | None]:
        rows = self.list_by_despacho(iddespacho)
        if not rows:
            return ESTADO_DEFAULT, None
        latest = rows[-1]
        return latest.get("estadonuevo", ESTADO_DEFAULT), latest.get("fechahora")

    def publish(
        self,
        *,
        iddespacho: int,
        estadonuevo: str,
        estadoanterior: str | None = None,
        idusuario: int | None = None,
    ) -> dict[str, Any]:
        if estadoanterior is None:
            estadoanterior, _ = self.get_current_estado(iddespacho)
        if estadonuevo not in ESTADO_ID_MAP:
            raise ValueError(f"Estado inválido: {estadonuevo}")
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            "idhistorialdespachounidad": self._next_id(),
            "iddespacho": iddespacho,
            "idestadodespacho": ESTADO_ID_MAP[estadonuevo],
            "estadoanterior": estadoanterior,
            "estadonuevo": estadonuevo,
            "fechahora": now,
            "fecha_actualizacion": now,
        }
        if idusuario is not None:
            payload["idusuario"] = idusuario
        self.kafka.publish(self.TOPIC, payload)
        return payload
