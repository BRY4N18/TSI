"""RF-SUSF-004 — generación de facturas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from core.repositories.suscripciones.factura_repository import FacturaRepository
from core.repositories.suscripciones.metodo_pago_repository import MetodoPagoRepository
from core.repositories.suscripciones.plan_repository import PlanRepository
from core.repositories.suscripciones.suscripcion_repository import SuscripcionRepository

TZ = ZoneInfo("America/Guayaquil")


class GeneracionFacturaService:
    def __init__(
        self,
        facturas: FacturaRepository | None = None,
        suscripciones: SuscripcionRepository | None = None,
        metodos: MetodoPagoRepository | None = None,
        plans: PlanRepository | None = None,
    ):
        self.facturas = facturas or FacturaRepository()
        self.suscripciones = suscripciones or SuscripcionRepository()
        self.metodos = metodos or MetodoPagoRepository()
        self.plans = plans or PlanRepository()

    def periodo_actual(self, suscripcion: dict[str, Any]) -> str:
        inicio = suscripcion.get("fecha_inicio")
        if isinstance(inicio, (int, float)):
            dt = datetime.fromtimestamp(inicio / 1000, tz=TZ)
        else:
            dt = datetime.now(TZ)
        return dt.strftime("%Y-%m")

    def para_suscripcion(self, suscripcion: dict[str, Any]) -> dict[str, Any] | None:
        if suscripcion.get("estado") != "Activa" or not suscripcion.get("activo"):
            return None
        metodo = self.metodos.find_activo(suscripcion["idcliente"])
        if not metodo:
            return None  # RN-018 — sin factura; caller puede notificar
        periodo = self.periodo_actual(suscripcion)
        existing = self.facturas.find_by_suscripcion_periodo(
            suscripcion["id_suscripcion"], periodo
        )
        if existing:
            return existing
        plan = self.plans.find_by_id(suscripcion["idplan"])
        nombre = plan["nombre"] if plan else "plan"
        monto = float(suscripcion.get("precio") or 0)
        return self.facturas.create(
            {
                "id_cliente": suscripcion["idcliente"],
                "id_suscripcion": suscripcion["id_suscripcion"],
                "idmetodopago": metodo["idmetodopago"],
                "periodo": periodo,
                "monto_base": monto,
                "desglose_cargos": [
                    {"concepto": f"Suscripcion plan {nombre}", "monto": monto}
                ],
            }
        )

    def ejecutar_batch(self) -> list[dict[str, Any]]:
        creadas = []
        for sus in self.suscripciones.list_elegibles_facturacion():
            fac = self.para_suscripcion(sus)
            if fac and fac.get("estado_pago") == "Pendiente" and fac.get("reintentos", 0) == 0:
                # newly created or pending day-0
                creadas.append(fac)
        return creadas
