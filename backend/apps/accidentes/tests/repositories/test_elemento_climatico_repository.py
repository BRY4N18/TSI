import pytest

from core.repositories.accidentes.elemento_climatico_repository import ElementoClimaticoRepository


@pytest.mark.repository
class TestElementoClimaticoRepository:
    def test_upsert_when_called_publishes_to_kafka(self, mock_kafka):
        # Arrange
        repo = ElementoClimaticoRepository()

        # Act
        result = repo.upsert(
            idaccidente="ACC-1",
            idperiododia=1,
            idestadoclima=2,
            idusuario=2,
        )

        # Assert
        assert result["idaccidente"] == "ACC-1"
        assert len(mock_kafka) == 1
