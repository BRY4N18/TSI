import pytest

from apps.cuentas_clientes.services.business_rbac_service import (
    BusinessRBACError,
    BusinessRBACService,
    ForbiddenRBACError,
)


@pytest.mark.service
class TestBusinessRBACService:
    def test_list_roles_when_admin_returns_roles(self, mock_pinot, mock_kafka):
        # Arrange
        service = BusinessRBACService()

        # Act
        roles = service.list_roles(admin_roles=["Administrador"])

        # Assert
        assert len(roles) >= 2

    def test_create_role_when_admin_creates_role(self, mock_pinot, mock_kafka):
        # Arrange
        service = BusinessRBACService()

        # Act
        role = service.create_role(
            {"rol": "Analista", "descripcion": "Analista de datos"},
            admin_roles=["Administrador"],
        )

        # Assert
        assert role["rol"] == "Analista"

    def test_create_role_when_duplicate_raises_error(self, mock_pinot, mock_kafka):
        # Arrange
        service = BusinessRBACService()

        # Act / Assert
        with pytest.raises(BusinessRBACError):
            service.create_role(
                {"rol": "Administrador", "descripcion": "dup"},
                admin_roles=["Administrador"],
            )

    def test_assign_role_when_not_admin_raises_forbidden(self, mock_pinot, mock_kafka):
        # Arrange
        service = BusinessRBACService()

        # Act / Assert
        with pytest.raises(ForbiddenRBACError):
            service.assign_role(1, 2, admin_roles=["Operador"])
