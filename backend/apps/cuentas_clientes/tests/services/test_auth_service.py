import pytest

from apps.cuentas_clientes.services.auth_service import AuthenticationError, AuthService


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

    def test_rechaza_login_si_la_organizacion_fue_dada_de_baja(self, mock_pinot, mock_kafka):
        """SRS §3.2.1: el login falla si la organización de la persona fue dada de baja.

        Esta validación no existía. El personal de un cliente cuyo contrato
        terminó seguía entrando y operando con normalidad: la baja marcaba la
        cuenta y expulsaba las sesiones abiertas, pero nada impedía abrir una
        nueva.
        """
        # Arrange — el usuario 3 pertenece a la cuenta 1; se da de baja la cuenta.
        from conftest import PINOT_STORE

        for cliente in PINOT_STORE["Dim_Cliente"]:
            if cliente["idcliente"] == 1:
                cliente["estado"] = "Dado de baja"

        # Act / Assert
        with pytest.raises(AuthenticationError):
            AuthService().login(gmail="cliente@tsi.com", password="password123")

    def test_el_personal_interno_de_tsi_no_se_ve_afectado(self, mock_pinot, mock_kafka):
        """Quien no pertenece a ninguna cuenta cliente entra con normalidad."""
        # Arrange — misma baja que el caso anterior.
        from conftest import PINOT_STORE

        for cliente in PINOT_STORE["Dim_Cliente"]:
            if cliente["idcliente"] == 1:
                cliente["estado"] = "Dado de baja"

        # Act
        result = AuthService().login(gmail="admin@tsi.com", password="password123")

        # Assert
        assert "accessToken" in result
