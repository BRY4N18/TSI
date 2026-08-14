"""Job — dunning reintentos D+3 / D+5 (RF-SUSF-005)."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from apps.suscripciones.services.cobro_service import CobroService
from core.repositories.suscripciones.factura_repository import FacturaRepository

TZ = ZoneInfo("America/Guayaquil")
logger = logging.getLogger(__name__)


def _parse_emision(valor) -> datetime | None:
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return datetime.fromtimestamp(valor / 1000, tz=TZ)
    return datetime.fromisoformat(str(valor).replace("Z", "+00:00")).astimezone(TZ)


def run_dunning(*, now: datetime | None = None) -> dict:
    now = now or datetime.now(TZ)
    facturas = FacturaRepository()
    cobro = CobroService()
    intentos = 0
    # El filtro va en SQL y el LIMIT es explícito: sin `LIMIT`, Pinot recorta a 10 filas
    # de la tabla entera, así que el ciclo de mora solo miraba diez facturas de todo el
    # sistema y el resto no se reintentaba ni se suspendía nunca.
    pendientes = facturas.pinot.query(
        "SELECT * FROM Fact_Factura WHERE estado_pago = %(estado)s "
        "ORDER BY fecha_emision DESC LIMIT %(limit)s",
        {"estado": "Pendiente", "limit": 10000},
    )
    for fac in list(pendientes or []):
        reintentos = int(fac.get("reintentos") or 0)
        emision = _parse_emision(fac.get("fecha_emision"))
        if not emision:
            continue
        dias = (now.date() - emision.astimezone(TZ).date()).days
        # Day 0 already tried at generation; D+3 → reintentos==1; D+5 → reintentos==2
        if dias >= 5 and reintentos == 2:
            cobro.intentar_factura(fac)
            intentos += 1
        elif dias >= 3 and reintentos == 1:
            cobro.intentar_factura(fac)
            intentos += 1
    logger.info("dunning_done", extra={"intentos": intentos})
    return {"intentos": intentos}
