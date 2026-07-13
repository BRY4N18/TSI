"""Baja de cuenta service — CU-O11."""

from __future__ import annotations

from apps.cuentas_clientes.services.audit_service import AuditService
from apps.cuentas_clientes.services.cuenta_access_service import CuentaAccessService
from apps.cuentas_clientes.services.cuenta_notificacion_service import CuentaNotificacionService
from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository
from core.repositories.cuentas_clientes.cuenta_usuario_repository import CuentaUsuarioRepository
from core.repositories.cuentas_clientes.session_repository import SessionRepository


class BajaCuentaError(Exception):
    """Account deactivation failed."""


class BajaCuentaService:
    """Logical account deactivation with session expulsion."""

    def __init__(
        self,
        cliente_repo: ClienteRepository | None = None,
        session_repo: SessionRepository | None = None,
        cuenta_usuario_repo: CuentaUsuarioRepository | None = None,
        access: CuentaAccessService | None = None,
        notificacion: CuentaNotificacionService | None = None,
        audit: AuditService | None = None,
    ):
        self.cliente_repo = cliente_repo or ClienteRepository()
        self.session_repo = session_repo or SessionRepository()
        self.cuenta_usuario_repo = cuenta_usuario_repo or CuentaUsuarioRepository()
        self.access = access or CuentaAccessService()
        self.notificacion = notificacion or CuentaNotificacionService()
        self.audit = audit or AuditService()

    def dar_baja(
        self,
        *,
        user_id: int,
        roles: list[str],
        cliente_id: int,
        motivo: str | None = None,
        ip_address: str | None = None,
    ) -> dict:
        self.access.require_admin_global(roles)

        cliente = self.cliente_repo.find_by_id(cliente_id)
        if not cliente:
            raise BajaCuentaError("Cuenta de cliente no encontrada")

        if cliente.get("estado") == "Dado de baja":
            return {
                "message": "Cuenta dada de baja",
                "estado": "Dado de baja",
                "sesiones_expulsadas": 0,
            }

        admin_local_id = cliente.get("admin_local_id")
        updated = self.cliente_repo.update(cliente_id, {"estado": "Dado de baja"})
        if not updated:
            raise BajaCuentaError("Cuenta de cliente no encontrada")

        sesiones_expulsadas = self.session_repo.expel_all_by_cliente(cliente_id)

        self.audit.log_baja_cuenta(
            user_id=user_id,
            cliente_id=cliente_id,
            motivo=motivo,
            ip_address=ip_address,
        )

        if admin_local_id:
            self.notificacion.notify_baja(
                cliente_id=cliente_id,
                admin_local_id=admin_local_id,
                actor_id=user_id,
            )

        return {
            "message": "Cuenta dada de baja",
            "estado": "Dado de baja",
            "sesiones_expulsadas": sesiones_expulsadas,
        }
