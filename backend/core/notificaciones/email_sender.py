"""Envío SMTP compartido — capa transversal usada por servicios de dominio
que notifican por correo (cuenta, onboarding, etc.). El registro de
auditoría de fallos queda a cargo de cada dominio (conoce el actor/contexto
a auditar); este módulo solo envía y loguea éxito/fallo del canal SMTP."""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger("tsi.notificaciones.email")


class EmailSendError(Exception):
    """Raised when el envío SMTP falla; el caller decide cómo auditar/reaccionar."""


class EmailNotificationSender:
    def send(self, *, event: str, cliente_id: int, gmail: str, subject: str, body: str) -> None:
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
                extra={"event": event, "to": gmail, "subject": subject, "idcliente": cliente_id},
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "smtp_failure",
                extra={"event": event, "to": gmail, "idcliente": cliente_id},
            )
            raise EmailSendError(str(exc)) from exc
