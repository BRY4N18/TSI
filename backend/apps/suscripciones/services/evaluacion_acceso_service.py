"""RN-SUSF-017 — evaluación de acceso al servicio."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Guayaquil")


class EvaluacionAccesoService:
    def acceso_permitido(self, suscripcion: dict[str, Any] | None, *, now: datetime | None = None) -> bool:
        if not suscripcion or not suscripcion.get("activo"):
            return False
        estado = suscripcion.get("estado")
        if estado == "Activa":
            return True
        if estado == "Suspendida":
            return False
        if estado == "Cancelada":
            now = now or datetime.now(TZ)
            fecha_fin = suscripcion.get("fecha_fin")
            if fecha_fin is None:
                return False
            if isinstance(fecha_fin, (int, float)):
                fin_dt = datetime.fromtimestamp(fecha_fin / 1000, tz=TZ)
            else:
                fin_dt = datetime.fromisoformat(str(fecha_fin).replace("Z", "+00:00")).astimezone(TZ)
            return now <= fin_dt
        return False
