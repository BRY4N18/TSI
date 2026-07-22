import time

import pytest

from apps.red_operativa.services.importacion_lote_unidad_service import (
    ImportacionLoteUnidadService,
)


@pytest.mark.slow
class TestImportacionLoteP95:
    def test_importar_500_filas_under_30_seconds(self, mock_pinot, mock_kafka):
        # Arrange
        service = ImportacionLoteUnidadService()
        filas = [
            {
                "idcliente": 1,
                "idcondado": 1,
                "tipopropiedad": "Externa",
                "placa": f"PERF-{i}",
                "contactoproveedor": "555",
                "unidademergencia": f"Unidad {i}",
                "tipounidademergencia": "Ambulancia",
            }
            for i in range(500)
        ]

        # Act
        start = time.perf_counter()
        result = service.importar(filas)
        elapsed = time.perf_counter() - start

        # Assert
        assert result["insertadas"] == 500
        assert elapsed < 30
