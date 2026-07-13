"""Dim_ParametrosDespacho repository — defaults RF-DES-010, Kafka write."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.accidentes.kafka_writer import KafkaWriter

DEFAULT_PARAMETROS: dict[str, Any] = {
    "timeout_respuesta_seg": 90,
    "peso_distancia_pct": 60,
    "peso_concordancia_pct": 25,
    "peso_disponibilidad_pct": 15,
    "prioridades_por_severidad": [
        {"idseveridad": 4, "orden_tipos": ["Ambulancia", "Patrulla", "Grua"]},
        {"idseveridad": 3, "orden_tipos": ["Ambulancia", "Grua", "Patrulla"]},
        {"idseveridad": 2, "orden_tipos": ["Grua", "Patrulla", "Ambulancia"]},
        {"idseveridad": 1, "orden_tipos": ["Patrulla", "Grua", "Ambulancia"]},
    ],
    "keywords_severidad_moderada": ["herido", "ambulancia"],
}


class ParametrosDespachoRepository:
    TOPIC = settings.KAFKA_TOPICS["parametros_despacho"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _normalize(self, row: dict[str, Any]) -> dict[str, Any]:
        prioridades = row.get("prioridades_por_severidad", DEFAULT_PARAMETROS["prioridades_por_severidad"])
        if isinstance(prioridades, str):
            prioridades = json.loads(prioridades)
        keywords = row.get("keywords_severidad_moderada", DEFAULT_PARAMETROS["keywords_severidad_moderada"])
        if isinstance(keywords, str):
            keywords = json.loads(keywords)
        return {
            "timeout_respuesta_seg": int(
                row.get("timeout_respuesta_seg", DEFAULT_PARAMETROS["timeout_respuesta_seg"])
            ),
            "peso_distancia_pct": int(
                row.get("peso_distancia_pct", DEFAULT_PARAMETROS["peso_distancia_pct"])
            ),
            "peso_concordancia_pct": int(
                row.get("peso_concordancia_pct", DEFAULT_PARAMETROS["peso_concordancia_pct"])
            ),
            "peso_disponibilidad_pct": int(
                row.get("peso_disponibilidad_pct", DEFAULT_PARAMETROS["peso_disponibilidad_pct"])
            ),
            "prioridades_por_severidad": prioridades,
            "keywords_severidad_moderada": keywords,
        }

    def get(self) -> dict[str, Any]:
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_ParametrosDespacho
            ORDER BY fecha_actualizacion DESC
            LIMIT 1
            """,
            {},
        )
        if not rows:
            return dict(DEFAULT_PARAMETROS)
        return self._normalize(rows[0])

    def publish_update(self, fields: dict[str, Any], *, idusuario: int) -> dict[str, Any]:
        current = self.get()
        merged = {**current, **fields}
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            "idparametrosdespacho": 1,
            "idusuario": idusuario,
            **merged,
            "prioridades_por_severidad": json.dumps(merged["prioridades_por_severidad"]),
            "keywords_severidad_moderada": json.dumps(merged["keywords_severidad_moderada"]),
            "fecha_actualizacion": now,
            "activo": True,
        }
        self.kafka.publish(self.TOPIC, payload)
        return self._normalize(payload)
