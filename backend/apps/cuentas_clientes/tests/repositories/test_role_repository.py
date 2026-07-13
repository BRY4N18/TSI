import pytest

from core.repositories.cuentas_clientes.role_repository import RoleRepository


@pytest.mark.repository
class TestRoleRepository:
    def test_get_user_roles_when_assigned_returns_role_names(self, mock_pinot, mock_kafka):
        # Arrange
        repo = RoleRepository()

        # Act
        roles = repo.get_user_roles(1)

        # Assert
        assert "Administrador" in roles

    def test_create_role_when_valid_publishes_to_kafka(self, mock_pinot, mock_kafka):
        # Arrange
        repo = RoleRepository()

        # Act
        role = repo.create_role({"rol": "Supervisor", "descripcion": "Supervisor de turno"})

        # Assert
        assert role["idrol"] > 2
        assert role["rol"] == "Supervisor"
        assert len(mock_kafka) == 1

    def test_assign_role_to_user_publishes_event(self, mock_pinot, mock_kafka):
        # Arrange
        repo = RoleRepository()

        # Act
        assignment = repo.assign_role_to_user(2, 1)

        # Assert
        assert assignment["idusuario"] == 2
        assert assignment["idrol"] == 1
        assert len(mock_kafka) == 1
