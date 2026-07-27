"""RF-SUSF-003 — solicitud / aprobación cambio de plan."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository
from core.repositories.suscripciones.plan_repository import PlanRepository
from core.repositories.suscripciones.solicitud_cambio_plan_repository import (
    SolicitudCambioPlanRepository,
)
from core.repositories.suscripciones.suscripcion_repository import SuscripcionRepository


class CambioPlanError(Exception):
    def __init__(self, code: str, detail: str, http_status: int = 400):
        self.code = code
        self.detail = detail
        self.http_status = http_status
        super().__init__(detail)


class CambioPlanService:
    def __init__(
        self,
        solicitudes: SolicitudCambioPlanRepository | None = None,
        suscripciones: SuscripcionRepository | None = None,
        plans: PlanRepository | None = None,
        clientes: ClienteRepository | None = None,
    ):
        self.solicitudes = solicitudes or SolicitudCambioPlanRepository()
        self.suscripciones = suscripciones or SuscripcionRepository()
        self.plans = plans or PlanRepository()
        self.clientes = clientes or ClienteRepository()

    def solicitar(self, *, idcliente: int, idplansolicitado: int, motivo: str = "") -> dict[str, Any]:
        sus = self.suscripciones.find_activa_by_cliente(idcliente)
        if not sus:
            raise CambioPlanError("no_suscripcion", "Sin suscripción activa")
        if self.solicitudes.find_pendiente(idcliente):
            raise CambioPlanError("conflict", "Ya hay solicitud Pendiente", 409)
        plan = self.plans.find_by_id(idplansolicitado)
        if not plan or not plan.get("activo"):
            raise CambioPlanError("plan_inactivo", "Plan destino inválido")
        if plan["idplan"] == sus["idplan"]:
            raise CambioPlanError("mismo_plan", "El plan solicitado es el actual")
        orden = {"Básico": 1, "Profesional": 2, "Empresarial": 3}
        actual = self.plans.find_by_id(sus["idplan"])
        nivel_actual = (actual or {}).get("nivel", "Básico")
        nivel_nuevo = plan.get("nivel", "Básico")
        es_upgrade = orden.get(nivel_nuevo, 0) > orden.get(nivel_actual, 0)
        sol = self.solicitudes.create(
            {
                "idcliente": idcliente,
                "idplanactual": sus["idplan"],
                "idplansolicitado": idplansolicitado,
                "motivo": motivo,
                "estado": "Pendiente",
            }
        )
        if es_upgrade:
            # Auto-aprobación de upgrade (OpenAPI / CU-O104)
            return self.aprobar(idsolicitud=sol["idsolicitud"], idadmin=0) or sol
        return sol


    def aprobar(self, *, idsolicitud: int, idadmin: int) -> dict[str, Any]:
        sol = self.solicitudes.find_by_id(idsolicitud)
        if not sol or sol.get("estado") != "Pendiente":
            raise CambioPlanError("not_found", "Solicitud no pendiente", 404)
        plan = self.plans.find_by_id(sol["idplansolicitado"])
        if not plan:
            raise CambioPlanError("plan_inactivo", "Plan destino no existe")
        sus = self.suscripciones.find_activa_by_cliente(sol["idcliente"])
        if not sus:
            raise CambioPlanError("no_suscripcion", "Sin suscripción")
        self.suscripciones.update(
            sus["id_suscripcion"],
            {"idplan": plan["idplan"], "precio": plan["precio"]},
        )
        self.clientes.update(sol["idcliente"], {"plan_suscripcion": plan["nombre"]})
        return self.solicitudes.update(
            idsolicitud,
            {
                "estado": "Aprobada",
                "idadminaprobador": idadmin,
                "fecha_resolucion": int(datetime.now(timezone.utc).timestamp() * 1000),
            },
        ) or sol

    def rechazar(self, *, idsolicitud: int, idadmin: int, motivo_rechazo: str) -> dict[str, Any]:
        sol = self.solicitudes.find_by_id(idsolicitud)
        if not sol or sol.get("estado") != "Pendiente":
            raise CambioPlanError("not_found", "Solicitud no pendiente", 404)
        return self.solicitudes.update(
            idsolicitud,
            {
                "estado": "Rechazada",
                "motivo_rechazo": motivo_rechazo,
                "idadminaprobador": idadmin,
                "fecha_resolucion": int(datetime.now(timezone.utc).timestamp() * 1000),
            },
        ) or sol
