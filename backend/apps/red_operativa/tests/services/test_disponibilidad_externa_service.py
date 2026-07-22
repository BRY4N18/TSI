import pytest

from apps.red_operativa.services.disponibilidad_externa_service import (
    DisponibilidadExternaService,
)


@pytest.mark.service
class TestDisponibilidadExternaService:
    def test_declarar_when_sin_despacho_activo_updates_estado(
        self, mock_pinot, mock_kafka, mock_unidad_emergencia
    ):
        # Arrange
        service = DisponibilidadExternaService()

        # Act
        result = service.declarar(
            idunidademergencia=mock_unidad_emergencia["idunidademergencia"],
            estadonuevo="Activa",
            idusuario_operador=2,
        )

        # Assert
        assert result["estadonuevo"] == "Activa"
        assert result["idusuario"] == 2

    def test_declarar_when_activa_con_despacho_activo_raises_value_error(
        self, mock_pinot, mock_kafka, mock_despacho_activo
    ):
        # Arrange
        service = DisponibilidadExternaService()

        # Act & Assert
        with pytest.raises(ValueError):
            service.declarar(
                idunidademergencia=mock_despacho_activo["idunidademergencia"],
                estadonuevo="Activa",
                idusuario_operador=2,
            )

    def test_declarar_when_en_mision_raises_permission_error(
        self, mock_pinot, mock_kafka, mock_unidad_emergencia
    ):
        # Arrange
        service = DisponibilidadExternaService()

        # Act & Assert
        with pytest.raises(PermissionError):
            service.declarar(
                idunidademergencia=mock_unidad_emergencia["idunidademergencia"],
                estadonuevo="En Misión",
                idusuario_operador=2,
            )

    def test_declarar_when_fuera_de_servicio_updates_estado(
        self, mock_pinot, mock_kafka, mock_unidad_emergencia
    ):
        # Arrange
        service = DisponibilidadExternaService()

        # Act
        result = service.declarar(
            idunidademergencia=mock_unidad_emergencia["idunidademergencia"],
            estadonuevo="Fuera de servicio",
            idusuario_operador=2,
        )

        # Assert
        assert result["estadonuevo"] == "Fuera de servicio"
