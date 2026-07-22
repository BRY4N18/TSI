"""Consumer O36 — re-asignación tras aborto de misión."""

from __future__ import annotations

import logging
from typing import Any

from apps.despacho.services.reasignacion_despacho_service import (
    ReasignacionDespachoService,
)

logger = logging.getLogger("tsi.despacho.consumer.despacho_abortado")


class DespachoAbortadoConsumer:
    def __init__(self, reasignacion: ReasignacionDespachoService | None = None):
        self.reasignacion = reasignacion or ReasignacionDespachoService()

    def handle(self, event: dict[str, Any]) -> dict[str, Any]:
        idaccidente = event.get("idaccidente")
        if not idaccidente:
            logger.warning("evento aborto sin idaccidente: %s", event)
            return {"reasignacion_iniciada": False}
        idusuario = int(event.get("idusuario", 0))
        result = self.reasignacion.ejecutar(idaccidente=idaccidente, idusuario=idusuario)
        logger.info("reasignacion tras aborto %s: %s", idaccidente, result)
        return result


def handle_despacho_abortado(event: dict[str, Any]) -> dict[str, Any]:
    return DespachoAbortadoConsumer().handle(event)
