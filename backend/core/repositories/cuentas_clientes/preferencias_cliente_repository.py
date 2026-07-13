"""Preferencias cliente repository — Dim_Preferencias_Cliente."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter


class PreferenciasClienteRepository:
    """Repository for Dim_Preferencias_Cliente entity."""

    TOPIC = settings.KAFKA_TOPICS["preferencias_cliente"]

    def __init__(
        self,
        pinot: PinotClient | None = None,
        kafka: KafkaWriter | None = None,
    ):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def find_by_cliente(self, cliente_id: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_Preferencias_Cliente
            WHERE id_cliente = %(id_cliente)s LIMIT 1
            """,
            {"id_cliente": cliente_id},
        )
        return rows[0] if rows else None

    def create(self, cliente_id: int, data: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        pref_id = self._next_id()
        payload = {
            "id_preferencia": pref_id,
            "id_cliente": cliente_id,
            "umbrales_alerta": data.get("umbrales_alerta", "{}"),
            "canales_notificacion": data.get("canales_notificacion", "email"),
            "telefono_sms": data.get("telefono_sms"),
            "zonas_geograficas": data.get("zonas_geograficas", "[]"),
            "destinatarios_reportes": data.get("destinatarios_reportes", ""),
            "frecuencia_reportes": data.get("frecuencia_reportes", ""),
            "formato_reportes": data.get("formato_reportes", ""),
            "activo": True,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def update(self, preferencia_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_Preferencias_Cliente
            WHERE id_preferencia = %(id_preferencia)s LIMIT 1
            """,
            {"id_preferencia": preferencia_id},
        )
        if not rows:
            return None
        existing = rows[0]
        now = datetime.now(timezone.utc).isoformat()
        payload = {**existing, **data, "fecha_actualizacion": now}
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def _next_id(self) -> int:
        rows = self.pinot.query(
            "SELECT MAX(id_preferencia) AS max_id FROM Dim_Preferencias_Cliente"
        )
        max_id = rows[0].get("max_id") if rows else 0
        return int(max_id or 0) + 1
