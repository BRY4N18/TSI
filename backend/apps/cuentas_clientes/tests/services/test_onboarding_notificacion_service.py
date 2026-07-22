from unittest.mock import patch

import pytest

from apps.cuentas_clientes.services.onboarding_notificacion_service import (
    OnboardingNotificacionService,
)


@pytest.mark.service
class TestOnboardingNotificacionService:
    @patch("core.notificaciones.email_sender.send_mail")
    def test_notify_invitacion_does_not_raise(self, mock_send, mock_pinot, mock_kafka):
        # Arrange
        service = OnboardingNotificacionService()

        # Act / Assert
        service.notify_invitacion(
            cliente_id=1,
            user_id=3,
            temp_password="temp123",
            actor_id=1,
        )

    @patch("core.notificaciones.email_sender.send_mail")
    def test_notify_reminder_does_not_raise(self, mock_send, mock_pinot, mock_kafka):
        # Arrange
        service = OnboardingNotificacionService()

        # Act / Assert
        service.notify_reminder(cliente_id=1, admin_local_id=3)
