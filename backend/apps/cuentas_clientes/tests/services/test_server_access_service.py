import pytest

from apps.cuentas_clientes.services.server_access_service import (
    ForbiddenServerAccessError,
    ServerAccessService,
)


@pytest.mark.service
class TestServerAccessService:
    def test_create_server_user_when_admin_succeeds(self, mock_pinot, mock_kafka):
        # Arrange
        service = ServerAccessService()

        # Act
        user = service.create_server_user(
            {"usuario": "infra-user", "contrasena": "secret"},
            caller_roles=["Administrador"],
        )

        # Assert
        assert user["usuario"] == "infra-user"

    def test_create_server_user_when_director_tecnologico_succeeds(self, mock_pinot, mock_kafka):
        # Arrange
        service = ServerAccessService()

        # Act
        user = service.create_server_user(
            {"usuario": "infra-user2", "contrasena": "secret"},
            caller_roles=["Director Tecnológico"],
        )

        # Assert
        assert user["usuario"] == "infra-user2"

    def test_create_server_user_when_operador_raises_forbidden(self, mock_pinot, mock_kafka):
        # Arrange
        service = ServerAccessService()

        # Act / Assert
        with pytest.raises(ForbiddenServerAccessError):
            service.create_server_user(
                {"usuario": "x", "contrasena": "y"},
                caller_roles=["Operador"],
            )
