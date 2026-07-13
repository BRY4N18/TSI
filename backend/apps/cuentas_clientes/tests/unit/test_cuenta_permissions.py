import pytest

from apps.cuentas_clientes.services.cuenta_access_service import CuentaAccessService


@pytest.mark.unit
class TestCuentaAccessService:
    def test_can_access_cuenta_when_admin_returns_true(self, mock_pinot, mock_kafka):
        # Arrange
        service = CuentaAccessService()

        # Act
        result = service.can_access_cuenta(user_id=1, roles=["Administrador"], cliente_id=1)

        # Assert
        assert result is True

    def test_is_admin_local_when_user_is_admin_returns_true(self, mock_pinot, mock_kafka):
        # Arrange
        service = CuentaAccessService()

        # Act
        result = service.is_admin_local(user_id=3, cliente_id=1)

        # Assert
        assert result is True
