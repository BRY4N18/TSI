import pytest

from core.repositories.evidencia.conductor_repository import ConductorRepository


@pytest.mark.repository
class TestConductorRepository:
    def test_create_when_valid_publishes_and_finds_by_identificacion(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        repo = ConductorRepository()

        # Act
        created = repo.create(
            {
                "identificacion": "0912345678",
                "nombres": "Ana",
                "apellidos": "Pérez",
            }
        )
        found = repo.find_by_identificacion("0912345678")

        # Assert
        assert created["idconductor"] == found["idconductor"]
        assert found["nombres"] == "Ana"
        assert len(mock_kafka) == 1
