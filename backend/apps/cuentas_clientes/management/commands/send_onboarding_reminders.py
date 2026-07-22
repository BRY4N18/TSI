"""Management command to send weekly onboarding reminders (RN-ONB-004)."""

from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.cuentas_clientes.services.onboarding_reminder_service import (
    OnboardingReminderService,
)


class Command(BaseCommand):
    help = "Send onboarding reminder emails for accounts incomplete after 30 days"

    def handle(self, *args, **options):
        service = OnboardingReminderService()
        sent = service.send_reminders()
        self.stdout.write(self.style.SUCCESS(f"Sent {sent} onboarding reminder(s)"))
