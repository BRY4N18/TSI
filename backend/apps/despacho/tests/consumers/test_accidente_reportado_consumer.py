import pytest

from apps.accidentes.domain_constants import ESTADO_REPORTADO
from apps.despacho.consumers.accidente_reportado_consumer import (
    AccidenteReportadoConsumer,
)
from apps.despacho.services.asignacion_inteligente_service import (
    AsignacionInteligenteService,
)


@pytest.mark.service
class TestAccidenteReportadoConsumer:
    def test_handle_when_reportado_triggers_asignacion(
        self, mock_pinot, mock_kafka, accidente_activo, unidad_con_estado_activa
    ):
        # Arrange
        consumer = AccidenteReportadoConsumer()

        # Act
        result = consumer.handle(
            {
                "idaccidente": accidente_activo,
                "estado": ESTADO_REPORTADO,
                "idusuario": 2,
            }
        )

        # Assert
        assert result is not None
        assert result["asignado"] is True
        assert result["iddespacho"] is not None
        assert len(mock_kafka) >= 2

    def test_handle_when_not_reportado_returns_none(self, mock_pinot, mock_kafka):
        # Arrange
        consumer = AccidenteReportadoConsumer()

        # Act
        result = consumer.handle({"idaccidente": "ACC-X", "estado": "ASIGNADO"})

        # Assert
        assert result is None

    def test_handle_when_no_candidatas_returns_asignado_false(
        self, mock_pinot, mock_kafka, accidente_activo
    ):
        # Arrange — sin unidad Activa
        consumer = AccidenteReportadoConsumer()

        # Act
        result = consumer.handle(
            {"idaccidente": accidente_activo, "estado": ESTADO_REPORTADO, "idusuario": 2}
        )

        # Assert
        assert result is not None
        assert result["asignado"] is False
