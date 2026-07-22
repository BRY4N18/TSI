import pytest

from core.repositories.despacho.historial_despacho_repository import (
    HistorialDespachoRepository,
)


@pytest.mark.repository
class TestHistorialDespachoRepository:
    def test_publish_when_first_record_defaults_estado_anterior_pendiente(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        repo = HistorialDespachoRepository()

        # Act
        record = repo.publish(iddespacho=1, estadonuevo="Confirmado")
        estado, _ = repo.get_current_estado(1)

        # Assert
        assert record["estadoanterior"] == "Pendiente"
        assert estado == "Confirmado"
        assert len(mock_kafka) == 1

    def test_list_by_despacho_when_multiple_returns_ordered(self, mock_pinot, mock_kafka):
        # Arrange
        repo = HistorialDespachoRepository()

        # Act
        repo.publish(iddespacho=2, estadonuevo="Pendiente")
        repo.publish(iddespacho=2, estadonuevo="Rechazado")
        rows = repo.list_by_despacho(2)

        # Assert
        assert len(rows) == 2
        assert rows[-1]["estadonuevo"] == "Rechazado"
