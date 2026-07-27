"""Job — mantenimiento activo=false post fecha_fin (Cancelada)."""

from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from core.repositories.suscripciones.suscripcion_repository import SuscripcionRepository

TZ = ZoneInfo("America/Guayaquil")
logger = logging.getLogger(__name__)


def run_mantenimiento_activo(*, now: datetime | None = None) -> dict:
    now = now or datetime.now(TZ)
    repo = SuscripcionRepository()
    desactivadas = 0
    rows = list(repo.pinot.query("SELECT * FROM Fact_Suscripcion", {}) or [])
    for sus in rows:
        if not (sus.get("activo") and sus.get("estado") == "Cancelada"):
            continue
        fecha_fin = sus.get("fecha_fin")
        if fecha_fin is None:
            continue
        if isinstance(fecha_fin, (int, float)):
            fin_dt = datetime.fromtimestamp(fecha_fin / 1000, tz=TZ)
        else:
            fin_dt = datetime.fromisoformat(str(fecha_fin).replace("Z", "+00:00")).astimezone(TZ)
        if now > fin_dt:
            repo.update(sus["id_suscripcion"], {"activo": False})
            desactivadas += 1
    logger.info("mantenimiento_activo_done", extra={"desactivadas": desactivadas})
    return {"desactivadas": desactivadas}
