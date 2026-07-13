import pytest

from core.repositories.cuentas_clientes.server_access_repository import ServerAccessRepository


@pytest.mark.repository
class TestServerAccessRepository:
    def test_create_server_user_when_valid_publishes_event(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ServerAccessRepository()

        # Act
        user = repo.create_server_user({"usuario": "dbadmin", "contrasena": "secret"})

        # Assert
        assert user["idusuariosservidor"] == 1
        assert user["usuario"] == "dbadmin"
        assert len(mock_kafka) == 1

    def test_create_server_role_when_valid_publishes_event(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ServerAccessRepository()

        # Act
        role = repo.create_server_role({"rolservidor": "dba", "descripcion": "DB admin"})

        # Assert
        assert role["idrolservidor"] == 1
        assert role["rolservidor"] == "dba"

    def test_assign_server_role_publishes_event(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ServerAccessRepository()
        repo.create_server_user({"usuario": "svc", "contrasena": "x"})
        repo.create_server_role({"rolservidor": "reader"})

        # Act
        assignment = repo.assign_server_role(1, 1)

        # Assert
        assert assignment["idusuariosservidor"] == 1
        assert assignment["idrolservidor"] == 1
