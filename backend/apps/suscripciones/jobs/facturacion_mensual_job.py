"""Job — facturación mensual (RF-SUSF-004)."""

from __future__ import annotations

import logging

from apps.suscripciones.services.cobro_service import CobroService
from apps.suscripciones.services.generacion_factura_service import GeneracionFacturaService

logger = logging.getLogger(__name__)


def run_facturacion_mensual() -> dict:
    generacion = GeneracionFacturaService()
    cobro = CobroService()
    creadas = generacion.ejecutar_batch()
    cobradas = 0
    for fac in creadas:
        if fac.get("estado_pago") == "Pendiente":
            # Sobre la factura recién creada, sin releerla: Pinot no la expone todavía
            # y el job entero moría con "factura no encontrada".
            cobro.intentar_factura(fac)
            cobradas += 1
    logger.info(
        "facturacion_mensual_done",
        extra={"facturas": len(creadas), "cobros_disparados": cobradas},
    )
    return {"facturas": len(creadas), "cobros_disparados": cobradas}
