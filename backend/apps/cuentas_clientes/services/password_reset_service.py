"""Password reset service — CU-O03 (catálogo vigente; ver spec CU-O06 histórico)."""

from __future__ import annotations

import secrets
import string

from apps.cuentas_clientes.services.audit_service import AuditService
from core.notificaciones.email_sender import EmailNotificationSender, EmailSendError
from core.repositories.cuentas_clientes.credential_repository import (
    CredentialRepository,
)
from core.repositories.cuentas_clientes.user_repository import UserRepository


class PasswordResetError(Exception):
    """Password reset failed."""


class PasswordResetService:
    """Generates temporary password, marks credential for change and emails it."""

    def __init__(
        self,
        user_repo: UserRepository | None = None,
        credential_repo: CredentialRepository | None = None,
        audit: AuditService | None = None,
        sender: EmailNotificationSender | None = None,
    ):
        self.user_repo = user_repo or UserRepository()
        self.credential_repo = credential_repo or CredentialRepository()
        self.audit = audit or AuditService()
        self.sender = sender or EmailNotificationSender()

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

        email_sent = self._send_temp_password_email(
            user_id=user["idusuario"], gmail=gmail, temp_password=temp_password
        )
        self.audit.log_password_reset(user["idusuario"], ip_address, success=True)

        return {
            "message": "Password reset email sent" if email_sent else "Password reset registered",
            "credentialStatus": "Cambio contraseña",
        }

    def _send_temp_password_email(self, *, user_id: int, gmail: str, temp_password: str) -> bool:
        subject = "Recuperación de contraseña — Tráfico Seguro Integral"
        body = (
            f"Solicitaste recuperar tu contraseña.\n\n"
            f"Contraseña temporal: {temp_password}\n\n"
            f"Debes cambiarla en tu próximo inicio de sesión."
        )
        try:
            self.sender.send(
                event="password_reset",
                cliente_id=user_id,
                gmail=gmail,
                subject=subject,
                body=body,
            )
            return True
        except EmailSendError as exc:
            self.audit.log_event(
                event_type="smtp_failure",
                user_id=user_id,
                ip_address=None,
                result="failure",
                details={"event": "password_reset", "error": str(exc)},
            )
            return False
