"""SMTP notifications for cuenta events — CU-O10, CU-O11."""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import send_mail

from apps.cuentas_clientes.services.audit_service import AuditService
from core.repositories.cuentas_clientes.user_repository import UserRepository

logger = logging.getLogger("tsi.notificaciones.cuenta")


class CuentaNotificacionService:
    """Sends email notifications; failures are logged without reverting operations."""

    def __init__(
        self,
        user_repo: UserRepository | None = None,
        audit: AuditService | None = None,
    ):
        self.user_repo = user_repo or UserRepository()
        self.audit = audit or AuditService()

    def notify_transferencia(
        self,
        *,
        cliente_id: int,
        nuevo_admin_id: int,
        anterior_admin_id: int,
        actor_id: int,
    ) -> None:
        recipients = [nuevo_admin_id, anterior_admin_id]
        self._send_to_users(
            event="transferencia_propiedad",
            cliente_id=cliente_id,
            actor_id=actor_id,
            user_ids=recipients,
            subject="Transferencia de administración de cuenta",
            body_template=(
                "La administración de la cuenta #{cliente_id} fue transferida.\n"
                "Si no reconoce este cambio, contacte al soporte de Tráfico Seguro Integral."
            ),
        )

    def notify_baja(
        self,
        *,
        cliente_id: int,
        admin_local_id: int,
        actor_id: int,
    ) -> None:
        self._send_to_users(
            event="baja_cuenta",
            cliente_id=cliente_id,
            actor_id=actor_id,
            user_ids=[admin_local_id],
            subject="Cuenta dada de baja",
            body_template=(
                "La cuenta #{cliente_id} fue dada de baja en Tráfico Seguro Integral.\n"
                "Las sesiones activas asociadas fueron cerradas."
            ),
        )

    def _send_to_users(
        self,
        *,
        event: str,
        cliente_id: int,
        actor_id: int,
        user_ids: list[int],
        subject: str,
        body_template: str,
    ) -> None:
        if not settings.EMAIL_HOST_USER:
            logger.warning(
                "smtp_skipped_not_configured",
                extra={"event": event, "idcliente": cliente_id},
            )
            return

        body = body_template.format(cliente_id=cliente_id)

        for user_id in user_ids:
            user = self.user_repo.find_by_id(user_id)
            if not user:
                continue
            gmail = user.get("gmail")
            if not gmail:
                continue
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
                    extra={
                        "event": event,
                        "to": gmail,
                        "subject": subject,
                        "idcliente": cliente_id,
                    },
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
