import pytest

from apps.soporte_cliente.services.asignacion_sla_service import AsignacionSLAService


@pytest.mark.service
class TestAsignacionSLAService:
    def test_asignar_when_regla_vigente_returns_sla_fields(self, mock_pinot, mock_kafka):
        # Arrange
        service = AsignacionSLAService()

        # Act
        resultado = service.asignar(idcliente=1, tipo_incidencia="tecnica", prioridad="alta")

        # Assert
        assert resultado is not None
        assert resultado["idslaconfig"] == 1
        assert resultado["sla_status"] == "en curso"
        assert resultado["sla_resolucion"] > resultado["sla_primera_respuesta"]

    def test_asignar_when_sin_suscripcion_activa_returns_none(self, mock_pinot, mock_kafka):
        # Arrange
        service = AsignacionSLAService()

        # Act
        resultado = service.asignar(idcliente=999, tipo_incidencia="tecnica", prioridad="alta")

        # Assert
        assert resultado is None

    def test_asignar_when_sin_regla_coincidente_returns_none(self, mock_pinot, mock_kafka):
        # Arrange
        service = AsignacionSLAService()

        # Act
        resultado = service.asignar(idcliente=1, tipo_incidencia="inexistente", prioridad="baja")

        # Assert
        assert resultado is None
