import pytest

from apps.suscripciones.services.catalogo_plan_service import (
    CatalogoPlanError,
    CatalogoPlanService,
)

pytestmark = pytest.mark.service


class TestCatalogoPlanService:
    def test_listar_activos(self, mock_pinot, mock_kafka):
        # Arrange / Act
        planes = CatalogoPlanService().listar()
        # Assert
        assert len(planes) >= 3

    def test_crear_invalido_nivel(self, mock_pinot, mock_kafka):
        # Arrange / Act / Assert
        with pytest.raises(CatalogoPlanError):
            CatalogoPlanService().crear(
                {
                    "nombre": "X",
                    "precio": 1,
                    "nivel": "Gold",
                    "limites": {
                        "unidades_max": 1,
                        "usuarios_max": 1,
                        "api_calls_mes": 1,
                    },
                }
            )
