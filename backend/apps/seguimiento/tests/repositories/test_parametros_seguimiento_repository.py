import pytest

from core.repositories.seguimiento.parametros_seguimiento_repository import (
    DEFAULT_PARAMETROS,
    ParametrosSeguimientoRepository,
)


@pytest.mark.repository
class TestParametrosSeguimientoRepository:
    def test_get_when_empty_returns_defaults(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ParametrosSeguimientoRepository()

        # Act
        params = repo.get()

        # Assert
        assert params["geofence_radio_metros"] == DEFAULT_PARAMETROS["geofence_radio_metros"]
        assert params["geofence_histéresis_seg"] == DEFAULT_PARAMETROS["geofence_histéresis_seg"]

    def test_publish_update_when_called_persists_kafka(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ParametrosSeguimientoRepository()

        # Act
        merged = repo.publish_update({"geofence_radio_metros": 150}, idusuario=2)

        # Assert
        assert merged["geofence_radio_metros"] == 150
        assert len(mock_kafka) == 1
