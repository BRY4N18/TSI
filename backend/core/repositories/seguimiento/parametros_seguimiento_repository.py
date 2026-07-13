"""Parámetros configurables de seguimiento — defaults RNF-SEG."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.accidentes.kafka_writer import KafkaWriter

DEFAULT_PARAMETROS: dict[str, Any] = {
    "gps_umbral_senal_perdida_seg": 60,
    "gps_job_intervalo_seg": 30,
    "geofence_radio_metros": 100,
    "geofence_histéresis_seg": 30,
    "gps_retencion_dias": 90,
}


class ParametrosSeguimientoRepository:
    TOPIC = settings.KAFKA_TOPICS["parametros_seguimiento"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def get(self) -> dict[str, Any]:
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_ParametrosSeguimiento
            ORDER BY fecha_actualizacion DESC
            LIMIT 1
            """,
            {},
        )
        if not rows:
            return dict(DEFAULT_PARAMETROS)
        row = rows[0]
        return {
            "gps_umbral_senal_perdida_seg": int(
                row.get("gps_umbral_senal_perdida_seg", DEFAULT_PARAMETROS["gps_umbral_senal_perdida_seg"])
            ),
            "gps_job_intervalo_seg": int(
                row.get("gps_job_intervalo_seg", DEFAULT_PARAMETROS["gps_job_intervalo_seg"])
            ),
            "geofence_radio_metros": int(
                row.get("geofence_radio_metros", DEFAULT_PARAMETROS["geofence_radio_metros"])
            ),
            "geofence_histéresis_seg": int(
                row.get("geofence_histéresis_seg", DEFAULT_PARAMETROS["geofence_histéresis_seg"])
            ),
            "gps_retencion_dias": int(
                row.get("gps_retencion_dias", DEFAULT_PARAMETROS["gps_retencion_dias"])
            ),
        }

    def publish_update(self, fields: dict[str, Any], *, idusuario: int) -> dict[str, Any]:
        merged = {**self.get(), **fields}
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            "idparametrosseguimiento": 1,
            "idusuario": idusuario,
            **merged,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return merged
