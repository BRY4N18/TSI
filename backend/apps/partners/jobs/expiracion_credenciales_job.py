"""Job RF-PON-006 — avisos y materializacion del vencimiento de credenciales.

El job NO es la fuente de verdad de la vigencia: `esta_vencida()` la deriva de
los datos, asi que una credencial vencida deja de servir aunque este job no
haya corrido. Aqui solo se avisa y se materializa `activo=false`.
"""

from __future__ import annotations

import logging

from apps.partners.services.expiracion_credencial_service import (
    ExpiracionCredencialService,
)

logger = logging.getLogger("tsi.partners.job.expiracion_credenciales")


def run_expiracion_credenciales_job() -> dict[str, int]:
    servicio = ExpiracionCredencialService()
    # Primero el aviso: si se procesaran antes las vencidas, una credencial que
    # cruza el umbral y vence en la misma pasada nunca llegaria a avisarse.
    avisos = servicio.avisar_proximas_a_vencer()
    vencidas = servicio.procesar_vencidas()

    resultado = {"avisadas": avisos["total"], "expiradas": vencidas["total"]}
    if resultado["avisadas"] or resultado["expiradas"]:
        logger.info(
            "job RF-PON-006: %d avisadas, %d expiradas",
            resultado["avisadas"],
            resultado["expiradas"],
        )
    return resultado
