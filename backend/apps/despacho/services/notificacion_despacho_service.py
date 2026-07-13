"""CU-O23 — notificación push/SMS con fail-fast."""

from __future__ import annotations

import logging
from typing import Any, Callable

from core.repositories.despacho.despacho_repository import DespachoRepository
from core.repositories.despacho.historial_despacho_repository import (
    ESTADO_PENDIENTE,
    ESTADO_RECHAZADO,
    HistorialDespachoRepository,
)
from core.repositories.despacho.notificacion_despacho_repository import (
    ESTADO_NO_ENTREGADA,
    ESTADO_NOTIFICADA,
    NotificacionDespachoRepository,
)

logger = logging.getLogger("tsi.despacho.notificacion")


class NotificacionDespachoService:
    def __init__(
        self,
        notificacion_repo: NotificacionDespachoRepository | None = None,
        despacho_repo: DespachoRepository | None = None,
        historial_repo: HistorialDespachoRepository | None = None,
        reasignacion: object | None = None,
        push_sender: Callable[[dict[str, Any]], bool] | None = None,
        sms_sender: Callable[[dict[str, Any]], bool] | None = None,
    ):
        self.notificaciones = notificacion_repo or NotificacionDespachoRepository()
        self.despachos = despacho_repo or DespachoRepository()
        self.historial = historial_repo or HistorialDespachoRepository()
        self._reasignacion = reasignacion
        self._push = push_sender or self._default_push
        self._sms = sms_sender or self._default_sms

    def notificar(
        self,
        *,
        idnotificaciondespacho: int,
        iddespacho: int,
        idaccidente: str,
    ) -> dict[str, Any]:
        payload = {
            "idnotificaciondespacho": idnotificaciondespacho,
            "idaccidente": idaccidente,
        }
        push_ok = self._try_twice(lambda: self._push(payload))
        sms_ok = self._try_twice(lambda: self._sms(payload))
        if push_ok or sms_ok:
            self.notificaciones.publish_update(
                idnotificaciondespacho,
                {"estadonotificaciondespacho": ESTADO_NOTIFICADA},
            )
            return {"estado": ESTADO_NOTIFICADA, "push": push_ok, "sms": sms_ok}
        self._marcar_fallo_entrega(idnotificaciondespacho, iddespacho, idaccidente)
        return {"estado": ESTADO_NO_ENTREGADA, "reasignacion_iniciada": True}

    def _marcar_fallo_entrega(
        self, idnotificaciondespacho: int, iddespacho: int, idaccidente: str
    ) -> None:
        self.notificaciones.publish_update(
            idnotificaciondespacho,
            {
                "estadonotificaciondespacho": ESTADO_NO_ENTREGADA,
                "motivo": "Fallo entrega push y SMS",
            },
        )
        self.despachos.publish_update(iddespacho, {"activo": False})
        self.historial.publish(
            iddespacho=iddespacho,
            estadonuevo=ESTADO_RECHAZADO,
            estadoanterior=ESTADO_PENDIENTE,
        )
        self._get_reasignacion().ejecutar(idaccidente=idaccidente, sincrono=True)

    def _get_reasignacion(self):
        if self._reasignacion is None:
            from apps.despacho.services.reasignacion_despacho_service import (
                ReasignacionDespachoService,
            )

            self._reasignacion = ReasignacionDespachoService()
        return self._reasignacion

    @staticmethod
    def _try_twice(fn: Callable[[], bool]) -> bool:
        if fn():
            return True
        return fn()

    @staticmethod
    def _default_push(_payload: dict[str, Any]) -> bool:
        logger.info("push despacho enviado (stub)")
        return True

    @staticmethod
    def _default_sms(_payload: dict[str, Any]) -> bool:
        logger.info("sms despacho enviado (stub)")
        return True
