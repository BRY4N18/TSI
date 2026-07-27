"""RF-SUSF-008 — renovación automática al fin de ciclo."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from dateutil.relativedelta import relativedelta

from core.repositories.suscripciones.suscripcion_repository import SuscripcionRepository
from apps.suscripciones.services.generacion_factura_service import GeneracionFacturaService
from apps.suscripciones.services.cobro_service import CobroService

TZ = ZoneInfo("America/Guayaquil")


class RenovacionService:
    def __init__(
        self,
        suscripciones: SuscripcionRepository | None = None,
        generacion: GeneracionFacturaService | None = None,
        cobro: CobroService | None = None,
    ):
        self.suscripciones = suscripciones or SuscripcionRepository()
        self.generacion = generacion or GeneracionFacturaService()
        self.cobro = cobro or CobroService()

    def _parse_fin(self, valor: Any) -> datetime | None:
        if valor is None:
            return None
        if isinstance(valor, (int, float)):
            return datetime.fromtimestamp(valor / 1000, tz=TZ)
        return datetime.fromisoformat(str(valor).replace("Z", "+00:00")).astimezone(TZ)

    def ejecutar_batch(self, *, now: datetime | None = None) -> list[dict[str, Any]]:
        now = now or datetime.now(TZ)
        resultados = []
        for sus in self.suscripciones.list_elegibles_renovacion():
            fin = self._parse_fin(sus.get("fecha_fin"))
            if fin is None or fin > now:
                continue
            if not sus.get("renovacionautomatica"):
                continue
            nueva_fin_dt = fin + relativedelta(months=1)
            nueva_fin = int(nueva_fin_dt.timestamp() * 1000)
            updated = self.suscripciones.update(
                sus["id_suscripcion"],
                {"fecha_fin": nueva_fin, "estado": "Activa"},
            )
            factura = self.generacion.para_suscripcion(updated or sus)
            if factura and factura.get("estado_pago") == "Pendiente":
                self.cobro.intentar(factura["id_factura"])
            resultados.append({"id_suscripcion": sus["id_suscripcion"], "fecha_fin": nueva_fin})
        return resultados
