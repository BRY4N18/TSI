"""Dim_UnidadEmergencia write repository — CRUD administrativo (CU-O54/56/57/58)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.red_operativa.kafka_writer import KafkaWriter


class UnidadEmergenciaRepository:
    """Repository for Dim_UnidadEmergencia entity (escritura administrativa)."""

    TOPIC = settings.KAFKA_TOPICS["unidad_emergencia_snapshot"]

    def __init__(
        self,
        pinot: PinotClient | None = None,
        kafka: KafkaWriter | None = None,
    ):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def find_by_id(self, idunidademergencia: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Dim_UnidadEmergencia WHERE idunidademergencia = %(idunidademergencia)s LIMIT 1",
            {"idunidademergencia": idunidademergencia},
        )
        return rows[0] if rows else None

    def find_by_placa_activa(self, placa: str) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Dim_UnidadEmergencia WHERE placa = %(placa)s AND activo = true",
            {"placa": placa},
        )
        return rows[0] if rows else None

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        idunidademergencia = self._next_id()
        payload = {
            "idunidademergencia": idunidademergencia,
            "idcliente": data["idcliente"],
            "idcondado": data["idcondado"],
            "tipopropiedad": data["tipopropiedad"],
            "placa": data["placa"],
            "capacidad": data.get("capacidad"),
            "contactoproveedor": data.get("contactoproveedor"),
            "unidademergencia": data["unidademergencia"],
            "tipounidademergencia": data["tipounidademergencia"],
            "activo": data.get("activo", True),
            "latitud": data.get("latitud"),
            "longitud": data.get("longitud"),
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def update(self, idunidademergencia: int, data: dict[str, Any]) -> dict[str, Any] | None:
        existing = self.find_by_id(idunidademergencia)
        if not existing:
            return None
        now = datetime.now(timezone.utc).isoformat()
        payload = {**existing, **data, "fecha_actualizacion": now}
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def _next_id(self) -> int:
        rows = self.pinot.query("SELECT MAX(idunidademergencia) AS max_id FROM Dim_UnidadEmergencia")
        max_id = rows[0].get("max_id") if rows else 0
        return int(max_id or 0) + 1

    def condado_exists(self, idcondado: int) -> bool:
        rows = self.pinot.query(
            "SELECT idcondado FROM Dim_Condado WHERE idcondado = %(idcondado)s LIMIT 1",
            {"idcondado": idcondado},
        )
        return bool(rows)
