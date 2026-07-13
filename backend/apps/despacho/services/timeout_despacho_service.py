"""CU-O35 — timeout de despacho sin respuesta."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from django.conf import settings

from core.repositories.accidentes.kafka_writer import KafkaWriter
from core.repositories.despacho.despacho_repository import DespachoRepository
from core.repositories.despacho.historial_despacho_repository import (
    ESTADO_PENDIENTE,
    ESTADO_TIMEOUT,
    HistorialDespachoRepository,
)
from core.repositories.despacho.notificacion_despacho_repository import (
    ESTADO_CONFIRMADA,
    ESTADO_RECHAZADA,
    NotificacionDespachoRepository,
)
from core.repositories.despacho.parametros_despacho_repository import ParametrosDespachoRepository

logger = logging.getLogger("tsi.despacho.timeout")


class TimeoutDespachoService:
    TOPIC = settings.KAFKA_TOPICS["despacho_timeout"]

    def __init__(
        self,
        despacho_repo: DespachoRepository | None = None,
        historial_repo: HistorialDespachoRepository | None = None,
        notificacion_repo: NotificacionDespachoRepository | None = None,
        parametros_repo: ParametrosDespachoRepository | None = None,
        kafka: KafkaWriter | None = None,
    ):
        self.despachos = despacho_repo or DespachoRepository()
        self.historial = historial_repo or HistorialDespachoRepository()
        self.notificaciones = notificacion_repo or NotificacionDespachoRepository()
        self.parametros = parametros_repo or ParametrosDespachoRepository()
        self.kafka = kafka or KafkaWriter()

    def procesar_ciclo(self, *, now_ms: int | None = None) -> list[dict[str, Any]]:
        params = self.parametros.get()
        timeout_ms = int(params["timeout_respuesta_seg"]) * 1000
        now = now_ms if now_ms is not None else int(
            datetime.now(timezone.utc).timestamp() * 1000
        )
        threshold = now - timeout_ms
        eventos: list[dict[str, Any]] = []
        for despacho in self.despachos.list_all_active():
            estado, _ = self.historial.get_current_estado(despacho["iddespacho"])
            if estado != ESTADO_PENDIENTE:
                continue
            if self._notificacion_respondida(despacho):
                continue
            fechahora = int(despacho.get("fechahoradespacho", 0))
            if fechahora > threshold:
                continue
            evento = self._marcar_timeout(despacho, now)
            eventos.append(evento)
            logger.info("timeout despacho %s accidente %s", despacho["iddespacho"], despacho["idaccidente"])
        return eventos

    def marcar_timeout(self, *, iddespacho: int, now_ms: int | None = None) -> dict[str, Any]:
        despacho = self.despachos.find_by_id(iddespacho)
        if not despacho:
            raise LookupError("Despacho no encontrado")
        if not despacho.get("activo"):
            raise ValueError("Despacho ya inactivo")
        now = now_ms if now_ms is not None else int(
            datetime.now(timezone.utc).timestamp() * 1000
        )
        return self._marcar_timeout(despacho, now)

    def _marcar_timeout(self, despacho: dict[str, Any], now: int) -> dict[str, Any]:
        iddespacho = int(despacho["iddespacho"])
        self.despachos.publish_update(iddespacho, {"activo": False})
        self.historial.publish(
            iddespacho=iddespacho,
            estadonuevo=ESTADO_TIMEOUT,
            estadoanterior=ESTADO_PENDIENTE,
        )
        evento = {
            "idaccidente": despacho["idaccidente"],
            "iddespacho": iddespacho,
            "fechahora": now,
        }
        self.kafka.publish(self.TOPIC, evento)
        return evento

    def _notificacion_respondida(self, despacho: dict[str, Any]) -> bool:
        idnotif = despacho.get("idnotificaciondespacho")
        if idnotif is None:
            return False
        notif = self.notificaciones.find_by_id(int(idnotif))
        if not notif:
            return False
        estado = notif.get("estadonotificaciondespacho")
        return estado in (ESTADO_CONFIRMADA, ESTADO_RECHAZADA)
