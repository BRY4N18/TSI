"""Fact_NotificacionVentas — Pinot read + Kafka-only write + dedup helpers."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.cuentas_clientes.kafka_writer import KafkaWriter
from core.pinot.secuencia import siguiente_id


class NotificacionVentasRepository:
    TOPIC = settings.KAFKA_TOPICS["notificacion_ventas"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        payload = {
            **data,
            "idnotificacion": self._next_id(),
            "fechahoranotificacion": data.get("fechahoranotificacion", now),
            "fecha_actualizacion": now,
        }
        self.kafka.publish(self.TOPIC, payload)
        return payload

    def exists_dedup_dia_utc(
        self, *, id_prospecto: int, regladisparada: str, day_start_ms: int, day_end_ms: int
    ) -> bool:
        rows = self.pinot.query(
            "SELECT COUNT(*) AS count FROM Fact_NotificacionVentas "
            "WHERE id_prospecto = %(idp)s AND regladisparada = %(regla)s "
            "AND fechahoranotificacion >= %(start)s AND fechahoranotificacion < %(end)s",
            {
                "idp": id_prospecto,
                "regla": regladisparada,
                "start": day_start_ms,
                "end": day_end_ms,
            },
        )
        return int((rows[0].get("count") or 0) if rows else 0) > 0

    def list(
        self,
        *,
        idusuariogerentenotificado: int | None = None,
        regladisparada: str | None = None,
        id_prospecto: int | None = None,
        limit: int = 20,
        cursor: int | None = None,
    ) -> list[dict[str, Any]]:
        clauses = ["1 = 1"]
        params: dict[str, Any] = {"limit": limit}
        if idusuariogerentenotificado is not None:
            clauses.append("idusuariogerentenotificado = %(uid)s")
            params["uid"] = idusuariogerentenotificado
        if regladisparada:
            clauses.append("regladisparada = %(regla)s")
            params["regla"] = regladisparada
        if id_prospecto is not None:
            clauses.append("id_prospecto = %(idp)s")
            params["idp"] = id_prospecto
        if cursor is not None:
            clauses.append("idnotificacion > %(cursor)s")
            params["cursor"] = cursor
        sql = (
            f"SELECT * FROM Fact_NotificacionVentas WHERE {' AND '.join(clauses)} "
            "ORDER BY idnotificacion LIMIT %(limit)s"
        )
        return list(self.pinot.query(sql, params) or [])

    def _next_id(self) -> int:
        return siguiente_id(self.pinot, "Fact_NotificacionVentas", "idnotificacion")
