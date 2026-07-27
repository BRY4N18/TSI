"""Job — renovación automática (RF-SUSF-008)."""

from __future__ import annotations

import logging

from apps.suscripciones.services.renovacion_service import RenovacionService

logger = logging.getLogger(__name__)


def run_renovacion() -> dict:
    resultados = RenovacionService().ejecutar_batch()
    logger.info("renovacion_done", extra={"renovadas": len(resultados)})
    return {"renovadas": len(resultados)}
