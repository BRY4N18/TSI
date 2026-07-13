import pytest

from apps.despacho.consumers.despacho_timeout_consumer import DespachoTimeoutConsumer


@pytest.mark.service
class TestDespachoTimeoutConsumer:
    def test_handle_when_event_has_accidente_triggers_reasignacion(
        self, mock_pinot, mock_kafka, accidente_activo, unidad_con_estado_activa
    ):
        # Arrange
        consumer = DespachoTimeoutConsumer()

        # Act
        result = consumer.handle(
            {"idaccidente": accidente_activo, "iddespacho": 99, "fechahora": 1}
        )

        # Assert
        assert "reasignacion_iniciada" in result
