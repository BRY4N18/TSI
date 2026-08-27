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
    def send(
        self,
        *,
        event: str,
        cliente_id: int,
        gmail: str,
        subject: str,
        body: str,
        html_body: str | None = None,
    ) -> None:
        """Envía el aviso. Con `html_body` sale como multipart/alternative.

        `body` (texto plano) **nunca es opcional**, ni siquiera cuando hay
        HTML: es la parte que leen los clientes que no renderizan HTML y los
        lectores de pantalla que prefieren texto, y es lo que queda si el
        HTML se filtra. Un correo HTML sin su parte de texto llega vacío a
        esos destinatarios, así que el parámetro se mantiene obligatorio a
        propósito.
        """
        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            logger.warning(
                "smtp_skipped_not_configured",
                extra={"event": event, "idcliente": cliente_id},
            )
            raise EmailSendError("SMTP no configurado (EMAIL_HOST_USER/PASSWORD)")

        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[gmail],
                fail_silently=False,
                html_message=html_body,
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
