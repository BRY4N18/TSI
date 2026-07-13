import pytest

from core.repositories.evidencia.evidencia_foto_repository import EvidenciaFotoRepository


@pytest.mark.repository
class TestEvidenciaFotoRepository:
    def test_create_when_valid_publishes_and_reads_back(self, mock_pinot, mock_kafka):
        # Arrange
        repo = EvidenciaFotoRepository()

        # Act
        created = repo.create(
            idaccidente="ACC-1",
            idusuario=7,
            urlevidenciafoto="https://blob.test/ACC-1/1.jpg",
            fechahora=1_700_000_000_000,
        )
        rows = repo.list_by_accidente("ACC-1")

        # Assert
        assert created["sincronizado"] is True
        assert len(rows) == 1
        assert rows[0]["idevidenciafoto"] == created["idevidenciafoto"]
        assert len(mock_kafka) == 1
