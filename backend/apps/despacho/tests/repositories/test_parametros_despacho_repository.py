import pytest

from core.repositories.despacho.parametros_despacho_repository import (
    DEFAULT_PARAMETROS,
    ParametrosDespachoRepository,
)


@pytest.mark.repository
class TestParametrosDespachoRepository:
    def test_get_when_empty_returns_defaults(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ParametrosDespachoRepository()

        # Act
        params = repo.get()

        # Assert
        assert params["timeout_respuesta_seg"] == DEFAULT_PARAMETROS["timeout_respuesta_seg"]
        assert params["peso_distancia_pct"] == DEFAULT_PARAMETROS["peso_distancia_pct"]

    def test_publish_update_when_called_persists_new_values(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ParametrosDespachoRepository()

        # Act
        repo.publish_update({"timeout_respuesta_seg": 120}, idusuario=1)
        params = repo.get()

        # Assert
        assert params["timeout_respuesta_seg"] == 120
        assert len(mock_kafka) == 1
