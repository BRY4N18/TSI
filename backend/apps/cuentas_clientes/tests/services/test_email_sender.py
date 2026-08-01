from unittest.mock import patch

import pytest

from core.notificaciones.email_sender import EmailNotificationSender, EmailSendError


@pytest.mark.service
class TestEmailNotificationSender:
    @patch("core.notificaciones.email_sender.send_mail")
    def test_send_when_configured_calls_send_mail(self, mock_send, settings):
        # Arrange
        settings.EMAIL_HOST_USER = "no-reply@tsi.com"
        settings.EMAIL_HOST_PASSWORD = "app-password"
        sender = EmailNotificationSender()

        # Act
        sender.send(event="test", cliente_id=1, gmail="a@b.com", subject="S", body="B")

        # Assert
        mock_send.assert_called_once()

    def test_send_when_no_configurado_raises_email_send_error(self, settings):
        # Arrange — sin pérdida silenciosa: el caller audita el fallo de canal
        settings.EMAIL_HOST_USER = ""
        settings.EMAIL_HOST_PASSWORD = ""
        sender = EmailNotificationSender()

        # Act / Assert
        with pytest.raises(EmailSendError, match="SMTP no configurado"):
            sender.send(event="test", cliente_id=1, gmail="a@b.com", subject="S", body="B")

    @patch("core.notificaciones.email_sender.send_mail", side_effect=Exception("smtp down"))
    def test_send_when_falla_raises_email_send_error(self, mock_send, settings):
        # Arrange
        settings.EMAIL_HOST_USER = "no-reply@tsi.com"
        settings.EMAIL_HOST_PASSWORD = "app-password"
        sender = EmailNotificationSender()

        # Act / Assert
        with pytest.raises(EmailSendError):
            sender.send(event="test", cliente_id=1, gmail="a@b.com", subject="S", body="B")
