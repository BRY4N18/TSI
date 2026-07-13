import pytest

from core.repositories.accidentes.elemento_fisico_repository import ElementoFisicoRepository


@pytest.mark.repository
class TestElementoFisicoRepository:
    def test_upsert_when_called_publishes_to_kafka(self, mock_kafka):
        # Arrange
        repo = ElementoFisicoRepository()

        # Act
        result = repo.upsert(idaccidente="ACC-1", idelementofisico=3, idusuario=2)

        # Assert
        assert result["idaccidente"] == "ACC-1"
        assert len(mock_kafka) == 1
