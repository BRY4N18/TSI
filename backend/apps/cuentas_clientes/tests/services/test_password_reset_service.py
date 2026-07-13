import pytest

from apps.cuentas_clientes.services.password_reset_service import (
    PasswordResetError,
    PasswordResetService,
)


@pytest.mark.service
class TestPasswordResetService:
    def test_request_reset_when_valid_email_succeeds(self, mock_pinot, mock_kafka):
        # Arrange
        service = PasswordResetService()

        # Act
        result = service.request_reset(gmail="admin@tsi.com")

        # Assert
        assert result["message"] == "Password reset email sent"
        assert result["credentialStatus"] == "Cambio contraseña"

    def test_request_reset_when_unknown_email_raises_error(self, mock_pinot, mock_kafka):
        # Arrange
        service = PasswordResetService()

        # Act / Assert
        with pytest.raises(PasswordResetError):
            service.request_reset(gmail="unknown@tsi.com")
