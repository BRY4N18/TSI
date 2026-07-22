"""Password reset service — CU-O06."""

from __future__ import annotations

import secrets
import string

from apps.cuentas_clientes.services.audit_service import AuditService
from core.repositories.cuentas_clientes.credential_repository import (
    CredentialRepository,
)
from core.repositories.cuentas_clientes.user_repository import UserRepository


class PasswordResetError(Exception):
    """Password reset failed."""


class PasswordResetService:
    """Generates temporary password and marks credential for change."""

    def __init__(
        self,
        user_repo: UserRepository | None = None,
        credential_repo: CredentialRepository | None = None,
        audit: AuditService | None = None,
    ):
        self.user_repo = user_repo or UserRepository()
        self.credential_repo = credential_repo or CredentialRepository()
        self.audit = audit or AuditService()

    def _generate_temporary_password(self, length: int = 12) -> str:
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def request_reset(self, *, gmail: str, ip_address: str | None = None) -> dict:
        user = self.user_repo.find_by_gmail(gmail)
        if not user or not user.get("activo", False):
            self.audit.log_password_reset(None, ip_address, success=False)
            raise PasswordResetError("Credenciales invalidas")

        temp_password = self._generate_temporary_password()
        result = self.credential_repo.reset_password(user["idusuario"], temp_password)
        if not result:
            self.audit.log_password_reset(user["idusuario"], ip_address, success=False)
            raise PasswordResetError("Credencial no encontrada")

        # In production: send email with temp_password via notification service
        self.audit.log_password_reset(user["idusuario"], ip_address, success=True)

        return {
            "message": "Password reset email sent",
            "credentialStatus": "Cambio contraseña",
        }
