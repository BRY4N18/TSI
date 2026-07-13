import pytest

from apps.cuentas_clientes.services.logout_service import LogoutError, LogoutService


@pytest.mark.service
class TestLogoutService:
    def test_logout_when_valid_session_closes_session(self, mock_pinot, mock_kafka):
        # Arrange
        service = LogoutService()

        # Act
        result = service.logout(session_id=1, user_id=1)

        # Assert
        assert result["sessionId"] == 1
        assert result["status"] == "Cierre sesion"
        assert result["closedAt"] is not None

    def test_logout_when_wrong_user_raises_error(self, mock_pinot, mock_kafka):
        # Arrange
        service = LogoutService()

        # Act / Assert
        with pytest.raises(LogoutError):
            service.logout(session_id=1, user_id=999)
