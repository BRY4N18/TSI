"""Dim_NotaAccidente repository."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.accidentes.kafka_writer import KafkaWriter


class NotaAccidenteRepository:
    TOPIC = settings.KAFKA_TOPICS["nota_accidente"]

    def __init__(self, kafka: KafkaWriter | None = None, pinot: PinotClient | None = None):
        self.kafka = kafka or KafkaWriter()
        self.pinot = pinot or PinotClient()

    def list_alertas(self, idaccidente: str, *, limit: int = 50) -> list[dict[str, Any]]:
        """Avisos del caso, del más reciente al más antiguo."""
        return self.pinot.query(
            """
            SELECT nota, fechahora FROM Dim_NotaAccidente
            WHERE idaccidente = %(idaccidente)s AND tipo = 'alerta'
            ORDER BY fechahora DESC
            LIMIT %(limit)s
            """,
            {"idaccidente": idaccidente, "limit": limit},
        )

    def latest_alerta_fechahora(self, *, idaccidente: str, contiene: str) -> int | None:
        """Marca de tiempo de la última alerta del caso cuyo texto contenga
        `contiene`. Sirve para no repetir un aviso que ya está puesto."""
        rows = self.pinot.query(
            """
            SELECT fechahora FROM Dim_NotaAccidente
            WHERE idaccidente = %(idaccidente)s
              AND tipo = 'alerta'
              AND nota LIKE %(patron)s
            ORDER BY fechahora DESC
            LIMIT 1
            """,
            {"idaccidente": idaccidente, "patron": f"%{contiene}%"},
        )
        return int(rows[0]["fechahora"]) if rows else None

    def create_escalamiento(
        self,
        *,
        idaccidente: str,
        idusuario: int,
        nota: str,
    ) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            "idnotaaccidentes": hash((idaccidente, now)) % 1_000_000,
            "idaccidente": idaccidente,
            "idusuario": idusuario,
            "nota": nota,
            "tipo": "escalamiento",
            "sincronizado": True,
            "activo": True,
            "fechahora": now,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def create_motivo(
        self,
        *,
        idaccidente: str,
        idusuario: int,
        nota: str,
    ) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            "idnotaaccidentes": hash((idaccidente, now, "motivo")) % 1_000_000,
            "idaccidente": idaccidente,
            "idusuario": idusuario,
            "nota": nota,
            "tipo": "motivo",
            "sincronizado": True,
            "activo": True,
            "fechahora": now,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def create_escalamiento_fallido(
        self,
        *,
        idaccidente: str,
        idusuario: int,
        nota: str,
    ) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            "idnotaaccidentes": hash((idaccidente, now, "escalamiento_fallido")) % 1_000_000,
            "idaccidente": idaccidente,
            "idusuario": idusuario,
            "nota": nota,
            "tipo": "escalamiento_fallido",
            "sincronizado": True,
            "activo": True,
            "fechahora": now,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def create_alerta(
        self,
        *,
        idaccidente: str,
        idusuario: int,
        nota: str,
    ) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            "idnotaaccidentes": hash((idaccidente, now, "alerta")) % 1_000_000,
            "idaccidente": idaccidente,
            "idusuario": idusuario,
            "nota": nota,
            "tipo": "alerta",
            "sincronizado": True,
            "activo": True,
            "fechahora": now,
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload
