import pytest

from core.repositories.cuentas_clientes.preferencias_cliente_repository import (
    PreferenciasClienteRepository,
)


@pytest.mark.repository
class TestPreferenciasClienteRepository:
    def test_find_by_cliente_when_exists_returns_preferencias(self, mock_pinot, mock_kafka):
        # Arrange
        repo = PreferenciasClienteRepository()

        # Act
        result = repo.find_by_cliente(1)

        # Assert
        assert result is not None
        assert result["id_cliente"] == 1

    def test_update_when_valid_publishes_to_kafka(self, mock_pinot, mock_kafka):
        # Arrange
        repo = PreferenciasClienteRepository()

        # Act
        updated = repo.update(1, {"telefono_sms": "3009998877"})

        # Assert
        assert updated is not None
        assert updated["telefono_sms"] == "3009998877"
        assert len(mock_kafka) == 1
