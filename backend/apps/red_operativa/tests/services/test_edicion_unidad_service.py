import pytest

from apps.red_operativa.services.edicion_unidad_service import EdicionUnidadService


@pytest.mark.service
class TestEdicionUnidadService:
    def test_editar_when_campo_no_critico_updates(self, mock_pinot, mock_kafka, mock_unidad_emergencia):
        # Arrange
        service = EdicionUnidadService()

        # Act
        result = service.editar(mock_unidad_emergencia["idunidademergencia"], {"capacidad": "8"})

        # Assert
        assert result["capacidad"] == "8"

    def test_editar_when_campo_critico_con_despacho_activo_sin_confirmar_raises(
        self, mock_pinot, mock_kafka, mock_despacho_activo
    ):
        # Arrange
        service = EdicionUnidadService()

        # Act & Assert
        with pytest.raises(ValueError):
            service.editar(
                mock_despacho_activo["idunidademergencia"],
                {"tipounidademergencia": "Patrulla"},
            )

    def test_editar_when_campo_critico_confirmado_updates(
        self, mock_pinot, mock_kafka, mock_despacho_activo
    ):
        # Arrange
        service = EdicionUnidadService()

        # Act
        result = service.editar(
            mock_despacho_activo["idunidademergencia"],
            {"tipounidademergencia": "Patrulla"},
            confirmar_edicion_critica=True,
        )

        # Assert
        assert result["tipounidademergencia"] == "Patrulla"

    def test_editar_when_sin_campos_editables_raises_key_error(
        self, mock_pinot, mock_kafka, mock_unidad_emergencia
    ):
        # Arrange
        service = EdicionUnidadService()

        # Act & Assert
        with pytest.raises(KeyError):
            service.editar(mock_unidad_emergencia["idunidademergencia"], {"idcliente": 99})
