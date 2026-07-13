import pytest

from apps.despacho.consumers.despacho_timeout_consumer import DespachoTimeoutConsumer
from apps.despacho.services.reasignacion_despacho_service import ReasignacionDespachoService


@pytest.mark.service
class TestReasignacionDespachoService:
    def test_ejecutar_when_vecino_available_reassigns(
        self, mock_pinot, mock_kafka, accidente_activo, unidad_con_estado_activa
    ):
        # Arrange
        from core.repositories.despacho.historial_estado_unidad_repository import (
            HistorialEstadoUnidadRepository,
        )

        HistorialEstadoUnidadRepository().append_estado(
            idunidademergencia=2,
            estadonuevo="Activa",
            idusuario=99,
            estadoanterior="Fuera de servicio",
        )
        svc = ReasignacionDespachoService()

        # Act
        result = svc.ejecutar(idaccidente=accidente_activo, incluir_vecinos=True)

        # Assert
        assert result["reasignacion_iniciada"] is True

    def test_ejecutar_when_no_units_creates_alerta(
        self, mock_pinot, mock_kafka, accidente_activo
    ):
        # Arrange
        svc = ReasignacionDespachoService()

        # Act
        result = svc.ejecutar(
            idaccidente=accidente_activo, incluir_vecinos=True, idusuario=2
        )

        # Assert
        assert result.get("alerta") is True


@pytest.mark.service
class TestDespachoTimeoutConsumer:
    def test_handle_triggers_reasignacion(
        self, mock_pinot, mock_kafka, accidente_activo, unidad_con_estado_activa
    ):
        # Arrange
        consumer = DespachoTimeoutConsumer()

        # Act
        result = consumer.handle(
            {"idaccidente": accidente_activo, "iddespacho": 1, "fechahora": 1}
        )

        # Assert
        assert "reasignacion_iniciada" in result
