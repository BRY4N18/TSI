"""Dim_EvidenciaFoto repository — Pinot read, Kafka write."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.accidentes.kafka_writer import KafkaWriter


class EvidenciaFotoRepository:
    TOPIC = settings.KAFKA_TOPICS["evidencia_foto"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _next_id(self) -> int:
        rows = self.pinot.query(
            "SELECT MAX(idevidenciafoto) AS max_id FROM Dim_EvidenciaFoto",
            {},
        )
        return int(rows[0]["max_id"] or 0) + 1 if rows else 1

    def list_by_accidente(
        self,
        idaccidente: str,
        *,
        limit: int = 20,
        cursor: int | None = None,
    ) -> list[dict[str, Any]]:
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_EvidenciaFoto
            WHERE idaccidente = %(idaccidente)s
            """,
            {"idaccidente": idaccidente},
        )
        rows = [r for r in rows if r.get("sincronizado") is True]
        rows.sort(key=lambda r: r.get("fechahora", 0), reverse=True)
        if cursor is not None:
            rows = [r for r in rows if r.get("idevidenciafoto", 0) < cursor]
        return rows[:limit]

    def find_by_id(self, idevidenciafoto: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            """
            SELECT * FROM Dim_EvidenciaFoto
            WHERE idevidenciafoto = %(idevidenciafoto)s
            LIMIT 1
            """,
            {"idevidenciafoto": idevidenciafoto},
        )
        return rows[0] if rows else None

    def create(
        self,
        *,
        idaccidente: str,
        idusuario: int,
        urlevidenciafoto: str,
        fechahora: int,
    ) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            "idevidenciafoto": self._next_id(),
            "idaccidente": idaccidente,
            "idusuario": idusuario,
            "urlevidenciafoto": urlevidenciafoto,
            "sincronizado": True,
            "fechahora": fechahora,
            "fecha_actualizacion": now,
            "activo": True,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload
