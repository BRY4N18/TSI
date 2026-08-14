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
from core.repositories.accidentes.estado_accidente_repository import ESTADO_NAMES
from core.repositories.despacho.despacho_repository import DespachoRepository

logger = logging.getLogger("tsi.despacho.consumer.accidente_reportado")


def _estado_del_evento(event: dict[str, Any]) -> str | None:
    """El evento real de `Fact_AccidenteTipoEstadoAccidente_topic` no lleva el
    nombre del estado: lleva `idtipoestadoincidente`, la FK al catálogo. Leer
    solo `estado` hacía que el handler ignorara en silencio todos los mensajes
    de producción."""
    idtipo = event.get("idtipoestadoincidente")
    if idtipo is not None:
        try:
            return ESTADO_NAMES.get(int(idtipo))
        except (TypeError, ValueError):
            logger.warning("idtipoestadoincidente ilegible: %r", idtipo)
            return None
    return event.get("estado") or event.get("estadoaccidente")


class AccidenteReportadoConsumer:
    def __init__(
        self,
        asignacion: AsignacionInteligenteService | None = None,
        reasignacion: ReasignacionDespachoService | None = None,
        despacho_repo: DespachoRepository | None = None,
    ):
        self.asignacion = asignacion or AsignacionInteligenteService()
        self.reasignacion = reasignacion or ReasignacionDespachoService()
        self.despachos = despacho_repo or DespachoRepository()

    def handle(self, event: dict[str, Any]) -> dict[str, Any] | None:
        estado = _estado_del_evento(event)
        if estado != ESTADO_REPORTADO:
            logger.debug("ignorando evento no REPORTADO: %s", estado)
            return None
        idaccidente = event.get("idaccidente")
        if not idaccidente:
            logger.warning("evento sin idaccidente: %s", event)
            return None
        # La entrega de Kafka es at-least-once: tras un reinicio del worker el
        # mismo evento puede volver. La asignación automática ocurre una sola
        # vez por caso, y tampoco debe duplicar un despacho que el operador ya
        # creó a mano mientras tanto.
        if self.despachos.list_by_accidente(idaccidente, activo=True):
            logger.info("%s ya tiene despacho activo, no se reasigna", idaccidente)
            return {"idaccidente": idaccidente, "asignado": False, "motivo": "ya_despachado"}
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
