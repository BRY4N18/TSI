"""RF-PON-003 — asignar el plan de acceso derivando el cupo (CU-O48).

El cupo NO se elige: se deriva del plan que el cliente ya contrato y se CONGELA
en el partner, igual que `Fact_Suscripcion.precio` congela el precio. Asi, un
cambio posterior del catalogo de planes no altera retroactivamente a un partner
ya incorporado — algo que importa porque ese cupo es la base del calculo de
excedente de CU-O54.
"""

from __future__ import annotations

from typing import Any

from apps.partners.domain_constants import (
    CAMBIO_ASIGNACION_PLAN,
    ESTADO_PLAN_ASIGNADO,
    ESTADO_REGISTRADO,
)
from core.repositories.partners.historial_acceso_repository import (
    HistorialAccesoRepository,
)
from core.repositories.partners.partner_repository import PartnerRepository
from core.repositories.partners.plan_read_repository import (
    PlanReadError,
    PlanReadRepository,
)


class AsignarPlanError(Exception):
    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(detail)


class AsignarPlanAccesoService:
    def __init__(
        self,
        partners: PartnerRepository | None = None,
        historial: HistorialAccesoRepository | None = None,
        planes: PlanReadRepository | None = None,
    ):
        self.partners = partners or PartnerRepository()
        self.historial = historial or HistorialAccesoRepository()
        self.planes = planes or PlanReadRepository()

    def asignar(self, *, idpartner: int, ejecutado_por: str) -> dict[str, Any]:
        """Congela el cupo del plan vigente en el partner.

        No acepta limites por parametro a proposito: si el cupo se pudiera
        enviar, dejaria de estar atado al plan contratado (RF-O48.3).
        """
        partner = self.partners.find_by_id(idpartner)
        if not partner:
            raise AsignarPlanError("not_found", "Partner no encontrado")

        # RN-PON-013: ninguna accion de habilitacion procede sobre un suspendido.
        if not partner.get("activo", False):
            raise AsignarPlanError(
                "partner_suspendido",
                "No se puede asignar plan a un partner suspendido",
            )

        try:
            cupo = self.planes.cupo_del_cliente(int(partner["idcliente"]))
        except PlanReadError as exc:
            # Se propaga el motivo real (sin suscripcion / plan incompleto) en
            # vez de asumir un cupo: un limite inventado se convertiria en
            # dinero mal cobrado sin que nadie lo note.
            raise AsignarPlanError(exc.code, exc.detail) from exc

        actualizado = self.partners.update(
            idpartner,
            {
                "planapi": cupo["nombre_plan"],
                "limitellamadasmes": cupo["api_calls_mes"],
                "limitellamadasminuto": cupo["api_calls_minuto"],
            },
        )

        self.historial.registrar(
            idpartner=idpartner,
            tipo_cambio=CAMBIO_ASIGNACION_PLAN,
            ejecutado_por=ejecutado_por,
            motivo=str(cupo["nombre_plan"]),
            estado_anterior=ESTADO_REGISTRADO,
            estado_nuevo=ESTADO_PLAN_ASIGNADO,
        )

        return {**actualizado, "estado": ESTADO_PLAN_ASIGNADO}
