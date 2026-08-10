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

    def test_handle_when_no_candidatas_escala_a_vecinos_y_deja_constancia(
        self, mock_pinot, mock_kafka, accidente_activo, pinot_store
    ):
        # Arrange — SRS 3.6.2: sin candidatas locales, el sistema no falla en
        # silencio; escala a vecinos (ReasignacionDespachoService) y, si
        # tampoco hay ahí, deja nota + alerta admin.
        consumer = AccidenteReportadoConsumer()

        # Act
        result = consumer.handle(
            {"idaccidente": accidente_activo, "estado": ESTADO_REPORTADO, "idusuario": 2}
        )

        # Assert
        assert result is not None
        assert result["asignado"] is False
        notas = [
            n
            for n in pinot_store["Dim_NotaAccidente"]
            if n.get("idaccidente") == accidente_activo
        ]
        assert any("Sin unidades disponibles" in n.get("nota", "") for n in notas)
