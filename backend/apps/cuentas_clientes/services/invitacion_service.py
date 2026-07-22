"""Reenvio de invitacion service — CU-O08."""

from __future__ import annotations

import secrets

from apps.cuentas_clientes.services.audit_service import AuditService
from apps.cuentas_clientes.services.onboarding_access_service import (
    OnboardingAccessService,
)
from apps.cuentas_clientes.services.onboarding_notificacion_service import (
    OnboardingNotificacionService,
)
from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository
from core.repositories.cuentas_clientes.credential_repository import (
    CredentialRepository,
)
from core.repositories.cuentas_clientes.user_repository import UserRepository


class InvitacionError(Exception):
    """Invitation resend failed."""


class InvitacionService:
    """Regenerates temporary password and sends invitation email."""

    def __init__(
        self,
        cliente_repo: ClienteRepository | None = None,
        user_repo: UserRepository | None = None,
        credential_repo: CredentialRepository | None = None,
        access: OnboardingAccessService | None = None,
        notificacion: OnboardingNotificacionService | None = None,
        audit: AuditService | None = None,
    ):
        self.cliente_repo = cliente_repo or ClienteRepository()
        self.user_repo = user_repo or UserRepository()
        self.credential_repo = credential_repo or CredentialRepository()
        self.access = access or OnboardingAccessService()
        self.notificacion = notificacion or OnboardingNotificacionService()
        self.audit = audit or AuditService()

    def reenviar(
        self,
        *,
        user_id: int,
        roles: list[str],
        cliente_id: int,
        target_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> dict:
        self.access.require_invitacion_access(
            user_id=user_id, roles=roles, cliente_id=cliente_id
        )
        cliente = self.cliente_repo.find_by_id(cliente_id)
        if not cliente:
            raise InvitacionError("Cuenta de cliente no encontrada")

        dest_id = target_user_id or cliente.get("admin_local_id")
        if not dest_id:
            raise InvitacionError("Usuario no encontrado")

        if dest_id != cliente.get("admin_local_id"):
            raise InvitacionError("Usuario no pertenece a la cuenta")

        user = self.user_repo.find_by_id(dest_id)
        if not user or not user.get("activo", False):
            raise InvitacionError("Usuario no encontrado")

        temp_password = secrets.token_urlsafe(12)
        cred = self.credential_repo.find_by_user_id(dest_id)
        if cred:
            self.credential_repo.reset_password(dest_id, temp_password)
        else:
            self.credential_repo.create_temporary(dest_id, temp_password)

        self.notificacion.notify_invitacion(
            cliente_id=cliente_id,
            user_id=dest_id,
            temp_password=temp_password,
            actor_id=user_id,
        )
        self.audit.log_reenvio_invitacion(
            user_id=user_id,
            target_user_id=dest_id,
            cliente_id=cliente_id,
            ip_address=ip_address,
        )

        return {
            "message": "Invitación reenviada",
            "id_usuario": dest_id,
        }
