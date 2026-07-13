import pytest

from apps.cuentas_clientes.services.auth_service import AuthService, AuthenticationError


@pytest.mark.service
class TestAuthService:
    def test_login_when_valid_credentials_returns_tokens(self, mock_pinot, mock_kafka):
        # Arrange
        service = AuthService()

        # Act
        result = service.login(gmail="admin@tsi.com", password="password123")

        # Assert
        assert "accessToken" in result
        assert "refreshToken" in result
        assert result["tokenType"] == "Bearer"
        assert result["expiresInSeconds"] == 3600
        assert result["profile"]["gmail"] == "admin@tsi.com"
        assert "Administrador" in result["profile"]["roles"]

    def test_login_when_wrong_password_raises_error(self, mock_pinot, mock_kafka):
        # Arrange
        service = AuthService()

        # Act / Assert
        with pytest.raises(AuthenticationError):
            service.login(gmail="admin@tsi.com", password="wrongpassword")

    def test_login_when_inactive_user_raises_error(self, mock_pinot, mock_kafka):
        # Arrange
        from core.repositories.cuentas_clientes.user_repository import UserRepository

        UserRepository().deactivate(1)
        service = AuthService()

        # Act / Assert
        with pytest.raises(AuthenticationError):
            service.login(gmail="admin@tsi.com", password="password123")
