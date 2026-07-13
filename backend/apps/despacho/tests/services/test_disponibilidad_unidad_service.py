import pytest

from apps.despacho.services.disponibilidad_unidad_service import DisponibilidadUnidadService


@pytest.mark.service
class TestDisponibilidadUnidadService:
    def test_consultar_when_no_history_returns_fuera_servicio(self, mock_pinot, mock_kafka):
        # Arrange
        service = DisponibilidadUnidadService()

        # Act
        data = service.consultar(1)

        # Assert
        assert data["estado_actual"] == "Fuera de servicio"
        assert data["incluido_en_despacho"] is False
        assert data["fechahora_ultimo_cambio"] is None

    def test_declarar_estado_when_valid_updates_state(
        self, mock_pinot, mock_kafka, unidad_con_estado_activa
    ):
        # Arrange
        service = DisponibilidadUnidadService()

        # Act
        result = service.declarar_estado(
            idunidademergencia=1,
            estadonuevo="Ocupada",
            idusuario=6,
        )
        consulta = service.consultar(1)

        # Assert
        assert result["estadoanterior"] == "Activa"
        assert result["estadonuevo"] == "Ocupada"
        assert consulta["estado_actual"] == "Ocupada"
        assert consulta["incluido_en_despacho"] is False
