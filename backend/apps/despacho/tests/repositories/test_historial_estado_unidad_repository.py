import pytest

from core.repositories.despacho.historial_estado_unidad_repository import (
    HistorialEstadoUnidadRepository,
)


@pytest.mark.repository
class TestHistorialEstadoUnidadRepository:
    def test_get_current_estado_when_no_history_returns_fuera_servicio(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        repo = HistorialEstadoUnidadRepository()

        # Act
        estado, fechahora = repo.get_current_estado(1)

        # Assert
        assert estado == "Fuera de servicio"
        assert fechahora is None

    def test_append_estado_when_valid_publishes(self, mock_pinot, mock_kafka):
        # Arrange
        repo = HistorialEstadoUnidadRepository()

        # Act
        record = repo.append_estado(
            idunidademergencia=1,
            estadonuevo="Activa",
            idusuario=6,
        )
        estado, _ = repo.get_current_estado(1)

        # Assert
        assert record["estadoanterior"] == "Fuera de servicio"
        assert estado == "Activa"
        assert len(mock_kafka) == 1
