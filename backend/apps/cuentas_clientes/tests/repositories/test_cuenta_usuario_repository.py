import pytest

from core.repositories.cuentas_clientes.cuenta_usuario_repository import (
    CuentaUsuarioRepository,
)


@pytest.mark.repository
class TestCuentaUsuarioRepository:
    def test_list_active_by_cliente_returns_admin_local_only(self, mock_pinot, mock_kafka):
        # Arrange
        repo = CuentaUsuarioRepository()

        # Act
        users = repo.list_active_by_cliente(1)

        # Assert
        assert len(users) == 1
        assert users[0]["gmail"] == "cliente@tsi.com"

    def test_user_belongs_to_cliente_when_admin_local_returns_true(self, mock_pinot, mock_kafka):
        # Arrange
        repo = CuentaUsuarioRepository()

        # Act
        result = repo.user_belongs_to_cliente(3, 1)

        # Assert
        assert result is True

    def test_user_belongs_to_cliente_when_not_admin_local_returns_false(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        repo = CuentaUsuarioRepository()

        # Act
        result = repo.user_belongs_to_cliente(4, 1)

        # Assert
        assert result is False

    def test_get_cliente_ids_for_user_returns_admin_cliente(self, mock_pinot, mock_kafka):
        # Arrange
        repo = CuentaUsuarioRepository()

        # Act
        ids = repo.get_cliente_ids_for_user(3)

        # Assert
        assert ids == [1]
