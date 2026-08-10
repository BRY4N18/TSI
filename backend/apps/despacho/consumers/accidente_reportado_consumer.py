"""Consumer O59 — dispara asignación automática al recibir estado REPORTADO."""

from __future__ import annotations

import logging
from typing import Any

from apps.accidentes.domain_constants import ESTADO_REPORTADO
from apps.despacho.services.asignacion_inteligente_service import (
    AsignacionInteligenteService,
)
from apps.despacho.services.reasignacion_despacho_service import (
    ReasignacionDespachoService,
)

logger = logging.getLogger("tsi.despacho.consumer.accidente_reportado")


class AccidenteReportadoConsumer:
    def __init__(
        self,
        asignacion: AsignacionInteligenteService | None = None,
        reasignacion: ReasignacionDespachoService | None = None,
    ):
        self.asignacion = asignacion or AsignacionInteligenteService()
        self.reasignacion = reasignacion or ReasignacionDespachoService()

    def handle(self, event: dict[str, Any]) -> dict[str, Any] | None:
        estado = event.get("estado") or event.get("estadoaccidente")
        if estado != ESTADO_REPORTADO:
            logger.debug("ignorando evento no REPORTADO: %s", estado)
            return None
        idaccidente = event.get("idaccidente")
        if not idaccidente:
            logger.warning("evento sin idaccidente: %s", event)
            return None
        idusuario = int(event.get("idusuario", 0))
        result = self.asignacion.ejecutar(idaccidente=idaccidente, idusuario=idusuario)
        if result is None:
            # SRS 3.6.2: "el sistema no falla en silencio ante la ausencia
            # total de unidades" — sin candidatas en el condado local, se
            # escala a zonas vecinas y, si tampoco hay ahí, se deja
            # constancia explícita (nota + alerta Admin), mismo camino que
            # usa la reasignación por rechazo/timeout.
            logger.info("sin candidatas locales para %s, escalando a vecinos", idaccidente)
            reasignado = self.reasignacion.ejecutar(
                idaccidente=idaccidente, idusuario=idusuario
            )
            despacho = reasignado.get("despacho")
            if despacho is None:
                return {"idaccidente": idaccidente, "asignado": False}
            logger.info(
                "despacho creado %s para %s (vía escalamiento a vecinos)",
                despacho.get("iddespacho"),
                idaccidente,
            )
            return {"idaccidente": idaccidente, "asignado": True, **despacho}
        logger.info("despacho creado %s para %s", result.get("iddespacho"), idaccidente)
        return {"idaccidente": idaccidente, "asignado": True, **result}


def handle_accidente_reportado(event: dict[str, Any]) -> dict[str, Any] | None:
    return AccidenteReportadoConsumer().handle(event)
