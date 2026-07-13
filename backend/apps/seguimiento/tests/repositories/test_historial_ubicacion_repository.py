import pytest

from core.repositories.seguimiento.historial_ubicacion_repository import HistorialUbicacionRepository


@pytest.mark.repository
class TestHistorialUbicacionRepository:
    def test_publish_when_valid_persists_to_kafka(self, mock_pinot, mock_kafka):
        # Arrange
        repo = HistorialUbicacionRepository()

        # Act
        record = repo.publish(
            idunidademergencia=1,
            idaccidente="ACC-1",
            latitud=19.43,
            longitud=-99.13,
            fechahora=1_700_000_000_000,
        )

        # Assert
        assert record["idhistorialubicacion"] == 1
        assert len(mock_kafka) == 1
        assert mock_kafka[0]["topic"].endswith("Dim_HistorialUbicacionUnidadEmergencia_topic")

    def test_list_by_unidad_when_multiple_returns_ordered(self, mock_pinot, mock_kafka):
        # Arrange
        repo = HistorialUbicacionRepository()
        repo.publish(
            idunidademergencia=1,
            idaccidente="ACC-1",
            latitud=1.0,
            longitud=2.0,
            fechahora=100,
        )
        repo.publish(
            idunidademergencia=1,
            idaccidente="ACC-1",
            latitud=3.0,
            longitud=4.0,
            fechahora=200,
        )

        # Act
        rows = repo.list_by_unidad(1)

        # Assert
        assert len(rows) == 2
        assert rows[0]["fechahora"] <= rows[1]["fechahora"]
