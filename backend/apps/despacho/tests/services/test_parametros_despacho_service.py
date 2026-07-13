import pytest

from apps.despacho.services.parametros_despacho_service import ParametrosDespachoService


@pytest.mark.service
class TestParametrosDespachoService:
    def test_obtener_returns_defaults(self, mock_pinot, mock_kafka):
        # Arrange
        svc = ParametrosDespachoService()

        # Act
        params = svc.obtener()

        # Assert
        assert params["timeout_respuesta_seg"] == 90

    def test_actualizar_when_valid_persists(self, mock_pinot, mock_kafka):
        # Arrange
        svc = ParametrosDespachoService()

        # Act
        updated = svc.actualizar(
            fields={"timeout_respuesta_seg": 60}, idusuario=9
        )

        # Assert
        assert updated["timeout_respuesta_seg"] == 60

    def test_actualizar_when_timeout_invalid_raises(self, mock_pinot, mock_kafka):
        # Arrange
        svc = ParametrosDespachoService()

        # Act / Assert
        with pytest.raises(ValueError):
            svc.actualizar(fields={"timeout_respuesta_seg": 10}, idusuario=9)
