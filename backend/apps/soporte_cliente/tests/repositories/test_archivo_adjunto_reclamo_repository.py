import pytest

from core.repositories.soporte.archivo_adjunto_reclamo_repository import (
    ArchivoAdjuntoReclamoRepository,
)


@pytest.mark.repository
class TestArchivoAdjuntoReclamoRepository:
    def test_append_when_valid_publishes(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ArchivoAdjuntoReclamoRepository()

        # Act
        record = repo.append(id_reclamo=1, urlarchivo="https://tsi-blob.local/x.jpg")

        # Assert
        assert record["idarchivoadjuntoreclamo"] == 1
        assert len(mock_kafka) == 1

    def test_list_by_ticket_when_multiple_returns_all(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ArchivoAdjuntoReclamoRepository()
        repo.append(id_reclamo=1, urlarchivo="a.jpg")
        repo.append(id_reclamo=1, urlarchivo="b.jpg")

        # Act
        items = repo.list_by_ticket(1)

        # Assert
        assert len(items) == 2
