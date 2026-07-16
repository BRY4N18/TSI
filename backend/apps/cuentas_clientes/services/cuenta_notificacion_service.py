"""SMTP notifications for cuenta events — CU-O10, CU-O11."""

from __future__ import annotations

from apps.cuentas_clientes.services.audit_service import AuditService
from core.notificaciones.email_sender import EmailNotificationSender, EmailSendError
from core.repositories.cuentas_clientes.user_repository import UserRepository


class CuentaNotificacionService:
    """Sends email notifications; failures are logged without reverting operations."""

    def __init__(
        self,
        user_repo: UserRepository | None = None,
        audit: AuditService | None = None,
        sender: EmailNotificationSender | None = None,
    ):
        self.user_repo = user_repo or UserRepository()
        self.audit = audit or AuditService()
        self.sender = sender or EmailNotificationSender()

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
        body = body_template.format(cliente_id=cliente_id)

        for user_id in user_ids:
            user = self.user_repo.find_by_id(user_id)
            if not user:
                continue
            gmail = user.get("gmail")
            if not gmail:
                continue
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
