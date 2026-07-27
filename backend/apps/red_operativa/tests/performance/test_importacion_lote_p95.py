import time
from unittest.mock import MagicMock

import pytest

from apps.red_operativa.services.importacion_lote_unidad_service import (
    ImportacionLoteUnidadService,
)


@pytest.mark.slow
class TestImportacionLoteP95:
    def test_importar_500_filas_under_30_seconds(self, mock_pinot, mock_kafka):
        # Arrange — SMTP/credenciales se mockean (I/O externo); mide validación + altas
        service = ImportacionLoteUnidadService()
        service.notificacion = MagicMock()
        service.credential_repo.create_temporary = MagicMock()
        filas = [
            {
                "idcondado": 1,
                "tipopropiedad": "Externa",
                "placa": f"PERF-{i}",
                "contactoproveedor": "555",
                "unidademergencia": f"Unidad {i}",
                "tipounidademergencia": "Ambulancia",
                "gmail": f"perf{i}@lote.test",
            }
            for i in range(500)
        ]

        # Act
        start = time.perf_counter()
        result = service.importar(filas, user_id=3, roles=["Cliente"])
        elapsed = time.perf_counter() - start

        # Assert
        assert result["insertadas"] == 500
        assert result["usuarios_creados"] == 500
        assert elapsed < 30
