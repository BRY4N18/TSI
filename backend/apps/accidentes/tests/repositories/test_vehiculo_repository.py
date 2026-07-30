import pytest

from core.repositories.evidencia.vehiculo_repository import VehiculoRepository


@pytest.mark.repository
class TestVehiculoRepository:
    def test_create_when_valid_publishes_and_finds_by_id(self, mock_pinot, mock_kafka):
        # Arrange
        repo = VehiculoRepository()

        # Act
        created = repo.create({"tipovehiculo": "Automóvil", "modelovehiculo": "Sedán"})
        found = repo.find_by_id(created["idvehiculo"])

        # Assert
        assert found["tipovehiculo"] == "Automóvil"
        assert len(mock_kafka) == 1
