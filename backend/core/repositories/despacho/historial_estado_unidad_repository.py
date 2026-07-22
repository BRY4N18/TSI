"""Fact_HistorialEstadoUnidad repository — append-only Kafka writes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.accidentes.kafka_writer import KafkaWriter

ESTADO_ACTIVA = "Activa"
ESTADO_OCUPADA = "Ocupada"
ESTADO_EN_MISION = "En Misión"
ESTADO_FUERA_SERVICIO = "Fuera de servicio"
ESTADO_DEFAULT = ESTADO_FUERA_SERVICIO

ESTADO_ID_MAP = {
    ESTADO_ACTIVA: 1,
    ESTADO_OCUPADA: 2,
    ESTADO_FUERA_SERVICIO: 3,
    ESTADO_EN_MISION: 4,
}

# "En Misión" solo la asigna el sistema al confirmar un despacho (confirmar_despacho_service.py)
# y solo se abandona al cerrar/abortar el caso (seguimiento-cierre-de-casos) — no es una transición
# manual disponible para la unidad vía /disponibilidad.
VALID_TRANSITIONS: dict[str, set[str]] = {
    ESTADO_ACTIVA: {ESTADO_OCUPADA, ESTADO_FUERA_SERVICIO, ESTADO_EN_MISION},
    ESTADO_OCUPADA: {ESTADO_ACTIVA, ESTADO_FUERA_SERVICIO},
    ESTADO_FUERA_SERVICIO: {ESTADO_ACTIVA},
    ESTADO_EN_MISION: {ESTADO_ACTIVA, ESTADO_FUERA_SERVICIO},
}


class HistorialEstadoUnidadRepository:
    TOPIC = settings.KAFKA_TOPICS["historial_estado_unidad"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _next_id(self) -> int:
        rows = self.pinot.query(
            """
            SELECT MAX(idhistorialestadosunidadesemergencias) AS max_id
            FROM Fact_HistorialEstadoUnidad
            """,
            {},
        )
        return int(rows[0]["max_id"] or 0) + 1 if rows else 1

    def list_by_unidad(
        self,
        idunidademergencia: int,
        *,
        limit: int = 20,
        cursor: int | None = None,
    ) -> list[dict[str, Any]]:
        rows = self.pinot.query(
            """
            SELECT * FROM Fact_HistorialEstadoUnidad
            WHERE idunidademergencia = %(idunidademergencia)s
            """,
            {"idunidademergencia": idunidademergencia},
        )
        rows.sort(
            key=lambda r: (
                r.get("fechahora", 0),
                r.get("idhistorialestadosunidadesemergencias", 0),
            ),
            reverse=True,
        )
        if cursor is not None:
            rows = [
                r
                for r in rows
                if r.get("idhistorialestadosunidadesemergencias", 0) < cursor
            ]
        return rows[:limit]

    def get_current_estado(self, idunidademergencia: int) -> tuple[str, int | None]:
        rows = self.list_by_unidad(idunidademergencia, limit=1)
        if not rows:
            return ESTADO_DEFAULT, None
        latest = rows[0]
        return latest.get("estadonuevo", ESTADO_DEFAULT), latest.get("fechahora")

    def append_estado(
        self,
        *,
        idunidademergencia: int,
        estadonuevo: str,
        idusuario: int,
        estadoanterior: str | None = None,
    ) -> dict[str, Any]:
        if estadoanterior is None:
            estadoanterior, _ = self.get_current_estado(idunidademergencia)
        if estadonuevo not in ESTADO_ID_MAP:
            raise ValueError(f"Estado inválido: {estadonuevo}")
        allowed = VALID_TRANSITIONS.get(estadoanterior, set())
        if estadonuevo != estadoanterior and estadonuevo not in allowed:
            raise ValueError(
                f"Transición inválida de {estadoanterior} a {estadonuevo}"
            )
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            "idhistorialestadosunidadesemergencias": self._next_id(),
            "idunidademergencia": idunidademergencia,
            "idestadounidademergencia": ESTADO_ID_MAP[estadonuevo],
            "estadoanterior": estadoanterior,
            "estadonuevo": estadonuevo,
            "idusuario": idusuario,
            "fechahora": now,
            "fecha_actualizacion": now,
            "activo": True,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload
