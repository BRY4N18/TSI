"""Onboarding reminder service — RN-ONB-004."""

from __future__ import annotations

from datetime import datetime, timezone

from apps.cuentas_clientes.services.audit_service import AuditService
from apps.cuentas_clientes.services.onboarding_notificacion_service import (
    OnboardingNotificacionService,
)
from core.pinot.client import PinotClient
from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository


class OnboardingReminderService:
    """Sends weekly reminders for incomplete onboarding after 30 days."""

    REMINDER_THRESHOLD_DAYS = 30

    def __init__(
        self,
        pinot: PinotClient | None = None,
        cliente_repo: ClienteRepository | None = None,
        notificacion: OnboardingNotificacionService | None = None,
        audit: AuditService | None = None,
    ):
        self.pinot = pinot or PinotClient()
        self.cliente_repo = cliente_repo or ClienteRepository()
        self.notificacion = notificacion or OnboardingNotificacionService()
        self.audit = audit or AuditService()

    def list_eligible_clientes(self) -> list[dict]:
        rows = self.pinot.query("SELECT * FROM Dim_Cliente")
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        threshold_ms = self.REMINDER_THRESHOLD_DAYS * 24 * 60 * 60 * 1000
        eligible = []
        for cliente in rows:
            if cliente.get("estado_onboarding") == "Completado":
                continue
            fecha_inicio = cliente.get("fecha_inicio_contrato")
            if fecha_inicio is None:
                continue
            if now_ms - int(fecha_inicio) < threshold_ms:
                continue
            admin_id = cliente.get("admin_local_id")
            if not admin_id:
                continue
            eligible.append(cliente)
        return eligible

    def send_reminders(self) -> int:
        sent = 0
        for cliente in self.list_eligible_clientes():
            admin_id = cliente["admin_local_id"]
            self.notificacion.notify_reminder(
                cliente_id=cliente["idcliente"],
                admin_local_id=admin_id,
            )
            self.audit.log_onboarding_reminder(
                cliente_id=cliente["idcliente"],
                admin_local_id=admin_id,
            )
            sent += 1
        return sent
