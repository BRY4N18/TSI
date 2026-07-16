"""SMTP notifications for onboarding events."""

from __future__ import annotations

from apps.cuentas_clientes.services.audit_service import AuditService
from core.notificaciones.email_sender import EmailNotificationSender, EmailSendError
from core.repositories.cuentas_clientes.user_repository import UserRepository


class OnboardingNotificacionService:
    """Sends onboarding invitation and reminder emails."""

    def __init__(
        self,
        user_repo: UserRepository | None = None,
        audit: AuditService | None = None,
        sender: EmailNotificationSender | None = None,
    ):
        self.user_repo = user_repo or UserRepository()
        self.audit = audit or AuditService()
        self.sender = sender or EmailNotificationSender()

    def notify_invitacion(
        self,
        *,
        cliente_id: int,
        user_id: int,
        temp_password: str,
        actor_id: int,
    ) -> None:
        user = self.user_repo.find_by_id(user_id)
        if not user:
            return
        gmail = user.get("gmail")
        if not gmail:
            return
        subject = "Invitación a Tráfico Seguro Integral"
        body = (
            f"Bienvenido a Tráfico Seguro Integral.\n\n"
            f"Su cuenta corporativa #{cliente_id} está lista.\n"
            f"Usuario: {gmail}\n"
            f"Contraseña temporal: {temp_password}\n\n"
            f"Debe cambiar su contraseña en el primer inicio de sesión."
        )
        self._send(
            event="invitacion_onboarding",
            cliente_id=cliente_id,
            actor_id=actor_id,
            gmail=gmail,
            subject=subject,
            body=body,
        )

    def notify_reminder(
        self,
        *,
        cliente_id: int,
        admin_local_id: int,
    ) -> None:
        user = self.user_repo.find_by_id(admin_local_id)
        if not user:
            return
        gmail = user.get("gmail")
        if not gmail:
            return
        subject = "Recordatorio: complete su onboarding"
        body = (
            f"Su onboarding de la cuenta #{cliente_id} aún no está completo.\n"
            f"Ingrese a la plataforma para finalizar la configuración."
        )
        self._send(
            event="onboarding_reminder",
            cliente_id=cliente_id,
            actor_id=admin_local_id,
            gmail=gmail,
            subject=subject,
            body=body,
        )

    def _send(
        self,
        *,
        event: str,
        cliente_id: int,
        actor_id: int,
        gmail: str,
        subject: str,
        body: str,
    ) -> None:
        try:
            self.sender.send(
                event=event,
                cliente_id=cliente_id,
                gmail=gmail,
                subject=subject,
                body=body,
            )
        except EmailSendError as exc:
            self.audit.log_smtp_failure(
                user_id=actor_id,
                cliente_id=cliente_id,
                event=event,
                error=str(exc),
            )
