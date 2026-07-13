"""SMTP notifications for onboarding events."""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import send_mail

from apps.cuentas_clientes.services.audit_service import AuditService
from core.repositories.cuentas_clientes.user_repository import UserRepository

logger = logging.getLogger("tsi.notificaciones.onboarding")


class OnboardingNotificacionService:
    """Sends onboarding invitation and reminder emails."""

    def __init__(
        self,
        user_repo: UserRepository | None = None,
        audit: AuditService | None = None,
    ):
        self.user_repo = user_repo or UserRepository()
        self.audit = audit or AuditService()

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
        if not settings.EMAIL_HOST_USER:
            logger.warning(
                "smtp_skipped_not_configured",
                extra={"event": event, "idcliente": cliente_id},
            )
            return
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[gmail],
                fail_silently=False,
            )
            logger.info(
                "smtp_send",
                extra={"event": event, "to": gmail, "idcliente": cliente_id},
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "smtp_failure",
                extra={"event": event, "to": gmail, "idcliente": cliente_id},
            )
            self.audit.log_smtp_failure(
                user_id=actor_id,
                cliente_id=cliente_id,
                event=event,
                error=str(exc),
            )
