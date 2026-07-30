"""Parámetros configurables de seguimiento — fuente: settings compartidos (no tabla de dominio).

Ownership: configuración operativa en `settings.SEGUIMIENTO_PARAMETROS`.
`Dim_ParametrosSeguimiento` / topic Kafka solo registran overrides auditables;
no cuentan como tabla de dominio del módulo seguimiento (flujo canónico Fase 4).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.accidentes.kafka_writer import KafkaWriter


def _defaults() -> dict[str, Any]:
    configured = getattr(settings, "SEGUIMIENTO_PARAMETROS", None) or {}
    return {
        "gps_umbral_senal_perdida_seg": int(
            configured.get("gps_umbral_senal_perdida_seg", 60)
        ),
        "gps_job_intervalo_seg": int(configured.get("gps_job_intervalo_seg", 30)),
        "geofence_radio_metros": int(configured.get("geofence_radio_metros", 100)),
        "geofence_histéresis_seg": int(configured.get("geofence_histéresis_seg", 30)),
        "gps_retencion_dias": int(configured.get("gps_retencion_dias", 90)),
    }


# Compat tests / imports existentes
DEFAULT_PARAMETROS = _defaults()


class ParametrosSeguimientoRepository:
    """Lee defaults de settings; overrides opcionales vía Kafka/Pinot (audit)."""

    TOPIC = settings.KAFKA_TOPICS["parametros_seguimiento"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def get(self) -> dict[str, Any]:
        base = _defaults()
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_ParametrosSeguimiento
            ORDER BY fecha_actualizacion DESC
            LIMIT 1
            """,
            {},
        )
        if not rows:
            return dict(base)
        row = rows[0]
        return {
            "gps_umbral_senal_perdida_seg": int(
                row.get(
                    "gps_umbral_senal_perdida_seg",
                    base["gps_umbral_senal_perdida_seg"],
                )
            ),
            "gps_job_intervalo_seg": int(
                row.get("gps_job_intervalo_seg", base["gps_job_intervalo_seg"])
            ),
            "geofence_radio_metros": int(
                row.get("geofence_radio_metros", base["geofence_radio_metros"])
            ),
            "geofence_histéresis_seg": int(
                row.get("geofence_histéresis_seg", base["geofence_histéresis_seg"])
            ),
            "gps_retencion_dias": int(
                row.get("gps_retencion_dias", base["gps_retencion_dias"])
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
