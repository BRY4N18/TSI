"""RF-SUSF-010 — alta inicial de suscripción."""

from __future__ import annotations

from typing import Any

from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository
from core.repositories.suscripciones.metodo_pago_repository import MetodoPagoRepository
from core.repositories.suscripciones.plan_repository import PlanRepository
from core.repositories.suscripciones.suscripcion_repository import SuscripcionRepository


class AltaSuscripcionError(Exception):
    def __init__(self, code: str, detail: str, http_status: int = 400):
        self.code = code
        self.detail = detail
        self.http_status = http_status
        super().__init__(detail)


class AltaSuscripcionService:
    def __init__(
        self,
        suscripciones: SuscripcionRepository | None = None,
        plans: PlanRepository | None = None,
        clientes: ClienteRepository | None = None,
        metodos: MetodoPagoRepository | None = None,
    ):
        self.suscripciones = suscripciones or SuscripcionRepository()
        self.plans = plans or PlanRepository()
        self.clientes = clientes or ClienteRepository()
        self.metodos = metodos or MetodoPagoRepository()

    def ejecutar(
        self,
        *,
        idcliente: int,
        idplan: int,
        renovacionautomatica: bool = True,
        generar_factura_si_metodo: bool = True,
    ) -> dict[str, Any]:
        if not self.clientes.find_by_id(idcliente):
            raise AltaSuscripcionError("cliente_not_found", "Dim_Cliente no existe", 404)
        existente = self.suscripciones.find_activa_by_cliente(idcliente)
        if existente and existente.get("activo"):
            raise AltaSuscripcionError(
                "conflict",
                "Ya existe una suscripción activo=true",
                409,
            )
        plan = self.plans.find_by_id(idplan)
        if not plan or not plan.get("activo"):
            raise AltaSuscripcionError("plan_inactivo", "Plan no disponible")
        suscripcion = self.suscripciones.create(
            {
                "idcliente": idcliente,
                "idplan": idplan,
                "precio": plan["precio"],
                "periodicidad": plan.get("periodicidad") or "Mensual",
                # Congelados al alta (mismo patrón que precio, ver suscripcion_repository.create).
                "nivel": plan.get("nivel"),
                "severidades_desbloqueadas": plan.get("severidades_desbloqueadas", "[]"),
                "carga_lote_habilitada": bool(plan.get("carga_lote_habilitada", False)),
                "renovacionautomatica": renovacionautomatica,
            }
        )
        # Sync denormalizado vía ClienteRepository (Kafka) — no publish directo
        self.clientes.update(idcliente, {"plan_suscripcion": plan["nombre"]})
        result: dict[str, Any] = {"suscripcion": suscripcion}
        if generar_factura_si_metodo and self.metodos.find_activo(idcliente):
            from apps.suscripciones.services.generacion_factura_service import (
                GeneracionFacturaService,
            )
            from apps.suscripciones.services.cobro_service import CobroService

            factura = GeneracionFacturaService().para_suscripcion(suscripcion)
            if factura:
                CobroService().intentar(factura["id_factura"])
                result["factura"] = factura
        return result
