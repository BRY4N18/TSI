"""RF-SUSF-008 — renovación automática al fin de ciclo."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository
from core.repositories.suscripciones.suscripcion_repository import SuscripcionRepository
from apps.suscripciones.services.cambio_plan_service import CambioPlanService
from apps.suscripciones.services.generacion_factura_service import GeneracionFacturaService
from apps.suscripciones.services.cobro_service import CobroService

TZ = ZoneInfo("America/Guayaquil")


class RenovacionService:
    def __init__(
        self,
        suscripciones: SuscripcionRepository | None = None,
        generacion: GeneracionFacturaService | None = None,
        cobro: CobroService | None = None,
        cambio_plan: CambioPlanService | None = None,
        clientes: ClienteRepository | None = None,
    ):
        self.suscripciones = suscripciones or SuscripcionRepository()
        self.generacion = generacion or GeneracionFacturaService()
        self.cobro = cobro or CobroService()
        self.cambio_plan = cambio_plan or CambioPlanService()
        self.clientes = clientes or ClienteRepository()

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
            nueva_fin_dt = self.suscripciones.add_cycle(fin, sus.get("periodicidad"))
            nueva_fin = int(nueva_fin_dt.timestamp() * 1000)
            # Una reducción de plan aprobada no se aplicó al aprobarse: se anotó como
            # programada para no quitarle al cliente lo que ya pagó (decisión #27).
            # Este es el momento en que toca aplicarla, en la misma escritura que
            # recorre el ciclo — el ciclo que empieza ya es el del plan nuevo, así que
            # la factura que se genera abajo sale con su precio.
            campos_plan, nombre_plan = self.cambio_plan.resolver_programado(sus)
            # `fecha_inicio` avanza al arranque del ciclo nuevo. No es la antigüedad
            # del cliente —eso es `Dim_Cliente.fecha_inicio_contrato`—, sino el inicio
            # del ciclo vigente, y de ella sale el período que se factura. Mientras se
            # quedaba clavada en el alta, todo ciclo calculaba el MISMO período, la
            # guarda de "no duplicar factura del período" lo bloqueaba, y la
            # suscripción se facturaba una sola vez en su vida.
            nueva_inicio = int(fin.timestamp() * 1000)
            updated = self.suscripciones.update(
                sus["id_suscripcion"],
                {
                    "fecha_inicio": nueva_inicio,
                    "fecha_fin": nueva_fin,
                    "estado": "Activa",
                    **campos_plan,
                },
            )
            if nombre_plan:
                self.clientes.update(sus["idcliente"], {"plan_suscripcion": nombre_plan})
            factura = self.generacion.para_suscripcion(updated or sus)
            if factura and factura.get("estado_pago") == "Pendiente":
                # Sobre la factura recién emitida, sin releerla: Pinot todavía no la
                # expone y el job entero moría con "factura no encontrada".
                self.cobro.intentar_factura(factura)
            resultados.append({"id_suscripcion": sus["id_suscripcion"], "fecha_fin": nueva_fin})
        return resultados
