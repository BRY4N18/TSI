import pytest

from core.repositories.seguimiento.unidad_snapshot_repository import (
    UnidadSnapshotRepository,
)


@pytest.mark.repository
class TestUnidadSnapshotRepository:
    def test_publish_snapshot_when_unit_exists_updates_kafka(self, mock_pinot, mock_kafka):
        # Arrange
        repo = UnidadSnapshotRepository()

        # Act
        record = repo.publish_snapshot(
            idunidademergencia=1,
            latitud=19.50,
            longitud=-99.20,
            fechahora=1_700_000_000_000,
        )

        # Assert
        assert record["latitud"] == 19.50
        assert record["longitud"] == -99.20
        assert len(mock_kafka) == 1
