"""Job O35 — escaneo periódico de despachos en timeout."""

from __future__ import annotations

import logging
from typing import Any

from apps.despacho.services.timeout_despacho_service import TimeoutDespachoService

logger = logging.getLogger("tsi.despacho.job.timeout")


def run_timeout_despacho_job() -> list[dict[str, Any]]:
    eventos = TimeoutDespachoService().procesar_ciclo()
    if eventos:
        logger.info("job O35 publicó %d eventos timeout", len(eventos))
    return eventos
