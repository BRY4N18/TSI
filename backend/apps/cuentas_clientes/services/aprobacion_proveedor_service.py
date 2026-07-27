"""Aprobar, rechazar o anular rechazo de solicitud — CU-O16."""

from __future__ import annotations

from typing import Any

from apps.cuentas_clientes.services.audit_service import AuditService
from apps.cuentas_clientes.services.onboarding_access_service import (
    OnboardingAccessService,
)
from apps.cuentas_clientes.services.onboarding_notificacion_service import (
    OnboardingNotificacionService,
)
from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository
from core.repositories.cuentas_clientes.user_repository import UserRepository

ESTADO_PENDIENTE = "Pendiente_Aprobación"
ESTADO_ACTIVO = "Activo"
ESTADO_RECHAZADO = "Rechazado"
ESTADO_RECHAZADO_ANULADO = "Rechazado_Anulado"


class AprobacionProveedorError(Exception):
    """Approval decision failed."""


class AprobacionProveedorService:
    """Admin approves, rejects, or soft-annuls provider self-registration requests."""

    def __init__(
        self,
        cliente_repo: ClienteRepository | None = None,
        user_repo: UserRepository | None = None,
        access: OnboardingAccessService | None = None,
        notificacion: OnboardingNotificacionService | None = None,
        audit: AuditService | None = None,
    ):
        self.cliente_repo = cliente_repo or ClienteRepository()
        self.user_repo = user_repo or UserRepository()
        self.access = access or OnboardingAccessService()
        self.notificacion = notificacion or OnboardingNotificacionService()
        self.audit = audit or AuditService()

    def listar_solicitudes(
        self, *, roles: list[str], estado: str = ESTADO_PENDIENTE
    ) -> list[dict[str, Any]]:
        self.access.require_admin_global(roles)
        allowed = {ESTADO_PENDIENTE, ESTADO_RECHAZADO}
        if estado not in allowed:
            raise AprobacionProveedorError("estado de filtro invalido")
        rows = self.cliente_repo.list_by_estado(estado)
        return [
            {
                "idcliente": r["idcliente"],
                "razon_social": r.get("razon_social", ""),
                "nit_identificacion": r.get("nit_identificacion", ""),
                "tipo": r.get("tipo", ""),
                "estado": r.get("estado"),
            }
            for r in rows
        ]

    def decidir(
        self,
        *,
        user_id: int,
        roles: list[str],
        cliente_id: int,
        decision: str,
        motivo: str | None = None,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        self.access.require_admin_global(roles)
        cliente = self.cliente_repo.find_by_id(cliente_id)
        if not cliente:
            raise AprobacionProveedorError("Cuenta de cliente no encontrada")
        if cliente.get("estado") != ESTADO_PENDIENTE:
            raise AprobacionProveedorError("La solicitud no esta pendiente de aprobacion")

        decision_norm = str(decision or "").strip().lower()
        admin_local_id = int(cliente.get("admin_local_id") or 0)

        if decision_norm == "aprobar":
            updated = self.cliente_repo.update_estado(
                cliente_id,
                estado=ESTADO_ACTIVO,
                estado_onboarding="Pendiente",
            )
            if not updated:
                raise AprobacionProveedorError("Cuenta de cliente no encontrada")
            self.audit.log_event(
                event_type="aprobacion_proveedor",
                user_id=user_id,
                ip_address=ip_address,
                result="success",
                details={"idcliente": cliente_id, "decision": "aprobar"},
            )
            if admin_local_id:
                self.notificacion.notify_aprobacion(
                    cliente_id=cliente_id,
                    admin_local_id=admin_local_id,
                    actor_id=user_id,
                )
            return {
                "idcliente": cliente_id,
                "estado": ESTADO_ACTIVO,
                "estado_onboarding": "Pendiente",
            }

        if decision_norm == "rechazar":
            motivo_clean = str(motivo or "").strip()
            if not motivo_clean:
                raise AprobacionProveedorError("motivo requerido al rechazar")
            updated = self.cliente_repo.update_estado(
                cliente_id,
                estado=ESTADO_RECHAZADO,
                estado_onboarding=None,
            )
            if not updated:
                raise AprobacionProveedorError("Cuenta de cliente no encontrada")
            self.audit.log_event(
                event_type="rechazo_proveedor",
                user_id=user_id,
                ip_address=ip_address,
                result="success",
                details={
                    "idcliente": cliente_id,
                    "decision": "rechazar",
                    "motivo": motivo_clean,
                },
            )
            if admin_local_id:
                self.notificacion.notify_rechazo(
                    cliente_id=cliente_id,
                    admin_local_id=admin_local_id,
                    actor_id=user_id,
                    motivo=motivo_clean,
                )
            return {
                "idcliente": cliente_id,
                "estado": ESTADO_RECHAZADO,
                "estado_onboarding": None,
            }

        raise AprobacionProveedorError("decision invalida")

    def anular_rechazo(
        self,
        *,
        user_id: int,
        roles: list[str],
        cliente_id: int,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        """Soft-annul rejected row so the same NIT can autorregistrarse de nuevo (fila nueva)."""
        self.access.require_admin_global(roles)
        cliente = self.cliente_repo.find_by_id(cliente_id)
        if not cliente:
            raise AprobacionProveedorError("Cuenta de cliente no encontrada")
        if cliente.get("estado") != ESTADO_RECHAZADO:
            raise AprobacionProveedorError("Solo se pueden anular solicitudes Rechazado")

        updated = self.cliente_repo.update_estado(
            cliente_id,
            estado=ESTADO_RECHAZADO_ANULADO,
            estado_onboarding=None,
        )
        if not updated:
            raise AprobacionProveedorError("Cuenta de cliente no encontrada")

        self.audit.log_event(
            event_type="anular_rechazo_proveedor",
            user_id=user_id,
            ip_address=ip_address,
            result="success",
            details={"idcliente": cliente_id, "estado": ESTADO_RECHAZADO_ANULADO},
        )
        return {
            "idcliente": cliente_id,
            "estado": ESTADO_RECHAZADO_ANULADO,
            "message": "Rechazo anulado; el NIT queda libre para un nuevo autorregistro",
        }
