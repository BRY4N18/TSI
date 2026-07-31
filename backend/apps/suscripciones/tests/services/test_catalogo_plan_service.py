import pytest

from apps.suscripciones.services.catalogo_plan_service import (
    CatalogoPlanError,
    CatalogoPlanService,
)

pytestmark = pytest.mark.service


class TestCatalogoPlanService:
    def test_listar_activos_paginado(self, mock_pinot, mock_kafka):
        # Arrange / Act
        result = CatalogoPlanService().listar(es_director=False)
        # Assert
        assert len(result["items"]) >= 3
        assert all(r["activo"] for r in result["items"])
        assert result["limit"] == 20
        assert "next_cursor" in result

    def test_listar_director_puede_ver_inactivos(self, mock_pinot, mock_kafka):
        result = CatalogoPlanService().listar(
            activo=False, es_director=True, limit=20
        )
        assert len(result["items"]) == 1
        assert result["items"][0]["activo"] is False

    def test_listar_director_omit_activo_es_todas(self, mock_pinot, mock_kafka):
        result = CatalogoPlanService().listar(es_director=True, limit=20)
        estados = {r["activo"] for r in result["items"]}
        assert True in estados and False in estados

    def test_listar_director_solo_activos_false_es_todas(self, mock_pinot, mock_kafka):
        result = CatalogoPlanService().listar(
            solo_activos=False, es_director=True, limit=20
        )
        estados = {r["activo"] for r in result["items"]}
        assert True in estados and False in estados

    def test_listar_no_director_fuerza_activos(self, mock_pinot, mock_kafka):
        result = CatalogoPlanService().listar(
            activo=False, es_director=False, limit=20
        )
        assert all(r["activo"] for r in result["items"])

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
