import time

import pytest

from core.repositories.red_operativa.unidad_emergencia_repository import (
    UnidadEmergenciaRepository,
)


@pytest.mark.slow
class TestDuplicadoPlacaP95:
    def test_find_by_placa_activa_under_1_second(
        self, mock_pinot, mock_kafka, mock_unidad_emergencia
    ):
        # Arrange
        repo = UnidadEmergenciaRepository()

        # Act
        start = time.perf_counter()
        repo.find_by_placa_activa(mock_unidad_emergencia["placa"])
        elapsed = time.perf_counter() - start

        # Assert
        assert elapsed < 1
