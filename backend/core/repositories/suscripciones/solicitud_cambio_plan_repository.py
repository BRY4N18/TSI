"""Fact_Solicitud_Cambio_Plan repository — RF-SUSF-003."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.pinot.client import PinotClient
from core.repositories.suscripciones.kafka_writer import KafkaWriter
from core.pinot.secuencia import siguiente_id


class SolicitudCambioPlanRepository:
    TOPIC = settings.KAFKA_TOPICS["solicitud_cambio_plan"]

    def __init__(self, pinot: PinotClient | None = None, kafka: KafkaWriter | None = None):
        self.pinot = pinot or PinotClient()
        self.kafka = kafka or KafkaWriter()

    def _now_ms(self) -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000)

    def _next_id(self) -> int:
        return siguiente_id(self.pinot, "Fact_Solicitud_Cambio_Plan", "idsolicitud")

    def find_by_id(self, idsolicitud: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Fact_Solicitud_Cambio_Plan WHERE idsolicitud = %(id)s",
            {"id": idsolicitud},
        )
        return rows[0] if rows else None

    def find_pendiente(self, idcliente: int) -> dict[str, Any] | None:
        # El filtro va en SQL y el LIMIT es explícito: sin `LIMIT`, Pinot recorta a
        # 10 filas de la tabla entera y la pendiente de este cliente puede quedar
        # fuera, con lo que se aceptaría una segunda solicitud simultánea.
        rows = self.pinot.query(
            "SELECT * FROM Fact_Solicitud_Cambio_Plan "
            "WHERE idcliente = %(idcliente)s AND estado = 'Pendiente' "
            "ORDER BY idsolicitud DESC LIMIT 100",
            {"idcliente": idcliente},
        )
        return rows[0] if rows else None

    def list(
        self,
        *,
        idcliente: int | None = None,
        estado: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        condiciones = []
        params: dict[str, Any] = {}
        if idcliente is not None:
            condiciones.append("idcliente = %(idcliente)s")
            params["idcliente"] = idcliente
        if estado:
            condiciones.append("estado = %(estado)s")
            params["estado"] = estado
        where = f"WHERE {' AND '.join(condiciones)} " if condiciones else ""
        rows = self.pinot.query(
            f"SELECT * FROM Fact_Solicitud_Cambio_Plan {where}"
            "ORDER BY idsolicitud DESC LIMIT %(limit)s",
            {**params, "limit": limit},
        )
        return list(rows or [])

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        record = {
            "idsolicitud": self._next_id(),
            "idcliente": data["idcliente"],
            "idplanactual": data["idplanactual"],
            "idplansolicitado": data["idplansolicitado"],
            "estado": data.get("estado", "Pendiente"),
            "motivo": data.get("motivo", ""),
            "motivo_rechazo": None,
            "idadminaprobador": data.get("idadminaprobador"),
            "fecha_solicitud": self._now_ms(),
            "fecha_resolucion": data.get("fecha_resolucion"),
            "fecha_actualizacion": self._now_ms(),
        }
        self.kafka.publish(self.TOPIC, record)
        return record

    def update(self, idsolicitud: int, changes: dict[str, Any]) -> dict[str, Any] | None:
        current = self.find_by_id(idsolicitud)
        if not current:
            return None
        return self.update_from(current, changes)

    def update_from(
        self, current: dict[str, Any], changes: dict[str, Any]
    ) -> dict[str, Any]:
        """Republica la fila completa a partir de una copia ya en memoria.

        La tabla es upsert por clave primaria, así que hay que reenviar todas las
        columnas. Esta variante existe para la auto-aprobación de un upgrade, que
        ocurre en la misma operación que el alta: releer por id contra Pinot ahí
        devuelve vacío durante 5-15 s y el cambio se perdía en silencio.
        """
        payload = {**current, **changes, "fecha_actualizacion": self._now_ms()}
        self.kafka.publish(self.TOPIC, payload)
        return payload
