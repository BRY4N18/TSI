import pytest

from apps.cuentas_clientes.services.password_reset_service import (
    PasswordResetError,
    PasswordResetService,
)
from core.notificaciones.email_sender import EmailSendError


class _FakeEmailSender:
    def __init__(self, fail: bool = False):
        self.fail = fail
        self.sent: list[dict] = []

    def send(self, *, event, cliente_id, gmail, subject, body):
        if self.fail:
            raise EmailSendError("smtp down")
        self.sent.append({"event": event, "gmail": gmail, "subject": subject, "body": body})


@pytest.mark.service
class TestPasswordResetService:
    def test_request_reset_when_valid_email_succeeds(self, mock_pinot, mock_kafka):
        # Arrange
        sender = _FakeEmailSender()
        service = PasswordResetService(sender=sender)

        # Act
        result = service.request_reset(gmail="admin@tsi.com")

        # Assert: el correo con la contraseña temporal realmente se envió.
        assert result["message"] == "Password reset email sent"
        assert result["credentialStatus"] == "Cambio contraseña"
        assert len(sender.sent) == 1
        assert sender.sent[0]["gmail"] == "admin@tsi.com"
        assert "Contraseña temporal" in sender.sent[0]["body"]

    def test_request_reset_when_unknown_email_raises_error(self, mock_pinot, mock_kafka):
        # Arrange
        service = PasswordResetService(sender=_FakeEmailSender())

        # Act / Assert
        with pytest.raises(PasswordResetError):
            service.request_reset(gmail="unknown@tsi.com")

    def test_request_reset_when_smtp_fails_still_registers_change(self, mock_pinot, mock_kafka):
        # Arrange: el fallo de SMTP no debe romper el flujo (la credencial ya quedó
        # marcada para cambio), pero el mensaje debe reflejar que no se envió correo.
        service = PasswordResetService(sender=_FakeEmailSender(fail=True))

        # Act
        result = service.request_reset(gmail="admin@tsi.com")

        # Assert
        assert result["message"] == "Password reset registered"
        assert result["credentialStatus"] == "Cambio contraseña"
