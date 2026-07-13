"""Consumer O36 async — re-asignación tras evento DespachoTimeout."""

from __future__ import annotations

import logging
from typing import Any

from apps.despacho.services.reasignacion_despacho_service import ReasignacionDespachoService

logger = logging.getLogger("tsi.despacho.consumer.despacho_timeout")


class DespachoTimeoutConsumer:
    def __init__(self, reasignacion: ReasignacionDespachoService | None = None):
        self.reasignacion = reasignacion or ReasignacionDespachoService()

    def handle(self, event: dict[str, Any]) -> dict[str, Any]:
        idaccidente = event.get("idaccidente")
        if not idaccidente:
            logger.warning("evento timeout sin idaccidente: %s", event)
            return {"reasignacion_iniciada": False}
        idusuario = int(event.get("idusuario", 0))
        result = self.reasignacion.ejecutar(
            idaccidente=idaccidente,
            idusuario=idusuario,
            sincrono=False,
        )
        logger.info("O36 timeout reasignación %s: %s", idaccidente, result)
        return result


def handle_despacho_timeout(event: dict[str, Any]) -> dict[str, Any]:
    return DespachoTimeoutConsumer().handle(event)
