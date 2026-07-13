import pytest

from apps.despacho.consumers.despacho_abortado_consumer import DespachoAbortadoConsumer


@pytest.mark.service
class TestDespachoAbortadoConsumer:
    def test_handle_when_event_has_accidente_triggers_reasignacion(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        unidad_con_estado_activa,
        despacho_confirmado_unidad,
    ):
        # Arrange
        consumer = DespachoAbortadoConsumer()
        event = {
            "iddespacho": despacho_confirmado_unidad["iddespacho"],
            "idaccidente": accidente_activo,
            "idusuario": 6,
        }

        # Act
        result = consumer.handle(event)

        # Assert
        assert "reasignacion_iniciada" in result

    def test_handle_when_sin_accidente_returns_false(
        self,
        mock_pinot,
        mock_kafka,
    ):
        # Arrange
        consumer = DespachoAbortadoConsumer()

        # Act
        result = consumer.handle({"iddespacho": 1})

        # Assert
        assert result["reasignacion_iniciada"] is False
