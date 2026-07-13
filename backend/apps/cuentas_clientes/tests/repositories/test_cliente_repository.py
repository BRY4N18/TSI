import pytest

from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository


@pytest.mark.repository
class TestClienteRepository:
    def test_find_by_id_when_exists_returns_cliente(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ClienteRepository()

        # Act
        result = repo.find_by_id(1)

        # Assert
        assert result is not None
        assert result["razon_social"] == "Empresa Demo S.A.S."

    def test_update_when_valid_publishes_to_kafka(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ClienteRepository()

        # Act
        updated = repo.update(1, {"nombre": "Empresa Actualizada"})

        # Assert
        assert updated is not None
        assert updated["nombre"] == "Empresa Actualizada"
        assert len(mock_kafka) == 1
