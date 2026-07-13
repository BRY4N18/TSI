import pytest

from apps.cuentas_clientes.services.user_management_service import (
    ForbiddenUserManagementError,
    UserManagementService,
)


@pytest.mark.service
class TestUserManagementService:
    def test_list_users_when_admin_returns_users(self, mock_pinot, mock_kafka):
        # Arrange
        service = UserManagementService()

        # Act
        users = service.list_users(admin_roles=["Administrador"])

        # Assert
        assert len(users) >= 2

    def test_create_user_when_admin_creates_user(self, mock_pinot, mock_kafka):
        # Arrange
        service = UserManagementService()
        data = {
            "nombres": "Test",
            "apellidos": "User",
            "gmail": "testuser@tsi.com",
            "password": "password123",
            "role_ids": [2],
        }

        # Act
        user = service.create_user(data, admin_roles=["Administrador"])

        # Assert
        assert user["gmail"] == "testuser@tsi.com"
        assert "Operador" in user["roles"]

    def test_create_user_when_not_admin_raises_forbidden(self, mock_pinot, mock_kafka):
        # Arrange
        service = UserManagementService()

        # Act / Assert
        with pytest.raises(ForbiddenUserManagementError):
            service.create_user({"gmail": "x@tsi.com"}, admin_roles=["Operador"])
