"""Fact_AccidenteTipoEstadoAccidente repository."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.accidentes.kafka_writer import KafkaWriter

# Fact_AccidenteTipoEstadoAccidente no guarda el nombre del estado como STRING:
# guarda idtipoestadoincidente (FK a Dim_TipoEstadoAccidente). Los IDs deben
# coincidir con el seed en database/seed_catalogos.py.
ESTADO_IDS: dict[str, int] = {
    "BORRADOR": 1,
    "REPORTADO": 2,
    "BUSCANDO_UNIDAD": 3,
    "ASIGNADO": 4,
    "EN_ATENCIÓN": 5,
    "CERRADO": 6,
    "DESCARTADO": 7,
    "FUSIONADO": 8,
}
ESTADO_NAMES: dict[int, str] = {v: k for k, v in ESTADO_IDS.items()}


class EstadoAccidenteRepository:
    TOPIC = settings.KAFKA_TOPICS["accidente_estado"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _next_id(self) -> int:
        rows = self.pinot.query(
            "SELECT MAX(idaccidentetipoestadoaccidente) AS max_id FROM Fact_AccidenteTipoEstadoAccidente",
            {},
        )
        return int(rows[0]["max_id"] or 0) + 1 if rows else 1

    def get_current_estado(self, idaccidente: str) -> str | None:
        rows = self.pinot.query(
            """
            SELECT idtipoestadoincidente FROM Fact_AccidenteTipoEstadoAccidente
            WHERE idaccidente = %(idaccidente)s
            ORDER BY fechahoramodificado DESC
            LIMIT 1
            """,
            {"idaccidente": idaccidente},
        )
        if not rows:
            return None
        return ESTADO_NAMES.get(int(rows[0]["idtipoestadoincidente"]))

    def get_history(self, idaccidente: str) -> list[dict[str, Any]]:
        rows = self.pinot.query(
            """
            SELECT idtipoestadoincidente, fechahoramodificado, idusuario
            FROM Fact_AccidenteTipoEstadoAccidente
            WHERE idaccidente = %(idaccidente)s
            ORDER BY fechahoramodificado ASC
            """,
            {"idaccidente": idaccidente},
        )
        for row in rows:
            row["estado"] = ESTADO_NAMES.get(int(row["idtipoestadoincidente"]))
        return rows

    def append_estado(self, *, idaccidente: str, estado: str, idusuario: int) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        history = self.get_history(idaccidente)
        if history and history[-1].get("fechahoramodificado", 0) >= now:
            now = history[-1]["fechahoramodificado"] + 1
        payload = {
            "idaccidentetipoestadoaccidente": self._next_id(),
            "idaccidente": idaccidente,
            "idtipoestadoincidente": ESTADO_IDS[estado],
            "idusuario": idusuario,
            "fechahoramodificado": now,
            "fecha_actualizacion": now,
            "activo": True,
        }
        self.kafka.publish(self.TOPIC, payload)
        payload["estado"] = estado
        return payload
