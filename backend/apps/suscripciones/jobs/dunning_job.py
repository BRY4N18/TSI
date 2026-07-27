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
    for fac in list(facturas.pinot.query("SELECT * FROM Fact_Factura", {}) or []):
        if fac.get("estado_pago") != "Pendiente":
            continue
        reintentos = int(fac.get("reintentos") or 0)
        emision = _parse_emision(fac.get("fecha_emision"))
        if not emision:
            continue
        dias = (now.date() - emision.astimezone(TZ).date()).days
        # Day 0 already tried at generation; D+3 → reintentos==1; D+5 → reintentos==2
        if dias >= 5 and reintentos == 2:
            cobro.intentar(fac["id_factura"])
            intentos += 1
        elif dias >= 3 and reintentos == 1:
            cobro.intentar(fac["id_factura"])
            intentos += 1
    logger.info("dunning_done", extra={"intentos": intentos})
    return {"intentos": intentos}
