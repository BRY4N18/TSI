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
        # Filtro, orden y tope viajan en el SQL: antes la base traía sin LIMIT y
        # Pinot la recortaba a 10 filas antes de que el filtro `sincronizado` y la
        # paginación se aplicaran en Python, así que un accidente con más de 10
        # fotos podía perder evidencia real de la galería.
        condiciones = ["idaccidente = %(idaccidente)s", "sincronizado = true"]
        params: dict[str, Any] = {"idaccidente": idaccidente, "limit": limit}
        if cursor is not None:
            condiciones.append("idevidenciafoto < %(cursor)s")
            params["cursor"] = cursor

        return self.pinot.query(
            f"""
            SELECT * FROM Dim_EvidenciaFoto
            WHERE {' AND '.join(condiciones)}
            ORDER BY fechahora DESC
            LIMIT %(limit)s
            """,
            params,
        )

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
