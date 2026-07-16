from unittest.mock import patch

import pytest

from core.notificaciones.email_sender import EmailNotificationSender, EmailSendError


@pytest.mark.service
class TestEmailNotificationSender:
    @patch("core.notificaciones.email_sender.send_mail")
    def test_send_when_configured_calls_send_mail(self, mock_send, settings):
        # Arrange
        settings.EMAIL_HOST_USER = "no-reply@tsi.com"
        sender = EmailNotificationSender()

        # Act
        sender.send(event="test", cliente_id=1, gmail="a@b.com", subject="S", body="B")

        # Assert
        mock_send.assert_called_once()

    def test_send_when_no_configurado_skips_silently(self, settings):
        # Arrange
        settings.EMAIL_HOST_USER = ""
        sender = EmailNotificationSender()

        # Act / Assert (no debe lanzar)
        sender.send(event="test", cliente_id=1, gmail="a@b.com", subject="S", body="B")

    @patch("core.notificaciones.email_sender.send_mail", side_effect=Exception("smtp down"))
    def test_send_when_falla_raises_email_send_error(self, mock_send, settings):
        # Arrange
        settings.EMAIL_HOST_USER = "no-reply@tsi.com"
        sender = EmailNotificationSender()

        # Act / Assert
        with pytest.raises(EmailSendError):
            sender.send(event="test", cliente_id=1, gmail="a@b.com", subject="S", body="B")
