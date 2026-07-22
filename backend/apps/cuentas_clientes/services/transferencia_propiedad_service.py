"""Transferencia de propiedad service — CU-O10."""

from __future__ import annotations

from apps.cuentas_clientes.services.audit_service import AuditService
from apps.cuentas_clientes.services.cuenta_access_service import CuentaAccessService
from apps.cuentas_clientes.services.cuenta_notificacion_service import (
    CuentaNotificacionService,
)
from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository
from core.repositories.cuentas_clientes.cuenta_usuario_repository import (
    CuentaUsuarioRepository,
)
from core.repositories.cuentas_clientes.role_repository import RoleRepository
from core.repositories.cuentas_clientes.user_repository import UserRepository


class TransferenciaPropiedadError(Exception):
    """Transfer failed."""


class TransferenciaPropiedadService:
    """Immediate admin_local_id transfer without acceptance flow."""

    def __init__(
        self,
        cliente_repo: ClienteRepository | None = None,
        cuenta_usuario_repo: CuentaUsuarioRepository | None = None,
        user_repo: UserRepository | None = None,
        role_repo: RoleRepository | None = None,
        access: CuentaAccessService | None = None,
        notificacion: CuentaNotificacionService | None = None,
        audit: AuditService | None = None,
    ):
        self.cliente_repo = cliente_repo or ClienteRepository()
        self.cuenta_usuario_repo = cuenta_usuario_repo or CuentaUsuarioRepository()
        self.user_repo = user_repo or UserRepository()
        self.role_repo = role_repo or RoleRepository()
        self.access = access or CuentaAccessService()
        self.notificacion = notificacion or CuentaNotificacionService()
        self.audit = audit or AuditService()

    def _cliente_role_users(self) -> list[dict]:
        users = self.user_repo.list_users(limit=100)
        elegibles = []
        for user in users:
            if not user.get("activo", False):
                continue
            if "Cliente" in self.role_repo.get_user_roles(user["idusuario"]):
                elegibles.append(user)
        return elegibles

    def list_usuarios_elegibles(
        self, *, user_id: int, roles: list[str], cliente_id: int
    ) -> list[dict]:
        self.access.require_access(user_id=user_id, roles=roles, cliente_id=cliente_id)
        self.access.require_admin_local(user_id=user_id, cliente_id=cliente_id)
        cliente = self.cliente_repo.find_by_id(cliente_id)
        admin_local_id = cliente.get("admin_local_id") if cliente else None
        usuarios = self._cliente_role_users()
        return [
            {
                "idusuario": u["idusuario"],
                "gmail": u["gmail"],
                "nombres": u["nombres"],
                "apellidos": u["apellidos"],
                "activo": u.get("activo", True),
                "es_admin_local_actual": u["idusuario"] == admin_local_id,
            }
            for u in usuarios
        ]

    def transferir(
        self,
        *,
        user_id: int,
        roles: list[str],
        cliente_id: int,
        nuevo_responsable_id: int,
        ip_address: str | None = None,
    ) -> dict:
        self.access.require_access(user_id=user_id, roles=roles, cliente_id=cliente_id)
        self.access.require_admin_local(user_id=user_id, cliente_id=cliente_id)
        cliente = self.access.ensure_cuenta_activa(cliente_id)

        anterior_admin_id = cliente.get("admin_local_id")
        if nuevo_responsable_id == anterior_admin_id:
            raise TransferenciaPropiedadError("El responsable ya es admin local")

        if not self._is_eligible_transfer_target(nuevo_responsable_id):
            raise TransferenciaPropiedadError("Usuario no pertenece a la cuenta")

        nuevo_user = self.user_repo.find_by_id(nuevo_responsable_id)
        if not nuevo_user or not nuevo_user.get("activo", False):
            raise TransferenciaPropiedadError("Usuario no activo")

        updated = self.cliente_repo.update(
            cliente_id, {"admin_local_id": nuevo_responsable_id}
        )
        if not updated:
            raise TransferenciaPropiedadError("Cuenta de cliente no encontrada")

        self.audit.log_transferencia(
            user_id=user_id,
            cliente_id=cliente_id,
            anterior_admin_id=anterior_admin_id,
            nuevo_admin_id=nuevo_responsable_id,
            ip_address=ip_address,
        )

        self.notificacion.notify_transferencia(
            cliente_id=cliente_id,
            nuevo_admin_id=nuevo_responsable_id,
            anterior_admin_id=anterior_admin_id,
            actor_id=user_id,
        )

        nombre = f"{nuevo_user['nombres']} {nuevo_user['apellidos']}".strip()
        return {
            "message": "Propiedad transferida",
            "nuevo_admin_local_id": nuevo_responsable_id,
            "nombre": nombre,
            "admin_local_anterior_id": anterior_admin_id,
        }

    def _is_eligible_transfer_target(self, user_id: int) -> bool:
        user = self.user_repo.find_by_id(user_id)
        if not user or not user.get("activo", False):
            return False
        return "Cliente" in self.role_repo.get_user_roles(user_id)
