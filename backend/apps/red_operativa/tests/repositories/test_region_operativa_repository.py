import pytest

from core.repositories.red_operativa.region_operativa_repository import (
    RegionOperativaRepository,
)


@pytest.mark.repository
class TestRegionOperativaRepository:
    def test_find_by_id_when_existente_returns_row(self, mock_pinot, mock_kafka):
        # Arrange
        repo = RegionOperativaRepository()

        # Act
        result = repo.find_by_id(1)

        # Assert
        assert result is not None
        assert result["idregionoperativa"] == 1

    def test_find_by_id_when_inexistente_returns_none(self, mock_pinot, mock_kafka):
        # Arrange
        repo = RegionOperativaRepository()

        # Act
        result = repo.find_by_id(999)

        # Assert
        assert result is None

    def test_create_publishes_event_and_returns_en_validacion(self, mock_pinot, mock_kafka):
        # Arrange
        repo = RegionOperativaRepository()

        # Act
        result = repo.create({"idestado": 2, "nombreregion": "Guadalajara"})

        # Assert
        assert result["estadoregion"] == "En_Validación"
        assert result["activo"] is True
        assert any(msg["topic"] == repo.TOPIC for msg in mock_kafka)

    def test_update_estadoregion_publishes_event(self, mock_pinot, mock_kafka):
        # Arrange
        repo = RegionOperativaRepository()

        # Act
        result = repo.update(1, {"estadoregion": "En_Alerta"})

        # Assert
        assert result["estadoregion"] == "En_Alerta"
        assert any(msg["topic"] == repo.TOPIC for msg in mock_kafka)

    def test_update_when_inexistente_returns_none(self, mock_pinot, mock_kafka):
        # Arrange
        repo = RegionOperativaRepository()

        # Act
        result = repo.update(999, {"estadoregion": "Despublicada"})

        # Assert
        assert result is None
