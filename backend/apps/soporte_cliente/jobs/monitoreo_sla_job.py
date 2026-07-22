"""Job CU-O96 — escaneo periódico de SLA y cierre automático (RNF-TIC-001, RN-TIC-004)."""

from __future__ import annotations

import logging

from apps.soporte_cliente.services.confirmar_cierre_service import ConfirmarCierreService
from apps.soporte_cliente.services.monitoreo_sla_service import MonitoreoSLAService

logger = logging.getLogger("tsi.soporte_cliente.job.monitoreo_sla")


def run_monitoreo_sla_job() -> dict[str, int]:
    resultado = MonitoreoSLAService().ejecutar_ciclo()
    cerrados = ConfirmarCierreService().cerrar_automaticamente_vencidos()
    resultado["cerrados_automaticamente"] = len(cerrados)
    if resultado["escalados"] or resultado["en_riesgo"] or resultado["cerrados_automaticamente"]:
        logger.info(
            "job CU-O96: %d escalados, %d en riesgo, %d cerrados automáticamente",
            resultado["escalados"],
            resultado["en_riesgo"],
            resultado["cerrados_automaticamente"],
        )
    return resultado
