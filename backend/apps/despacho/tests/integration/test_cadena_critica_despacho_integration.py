import pytest

from apps.accidentes.domain_constants import ESTADO_REPORTADO
from apps.despacho.consumers.accidente_reportado_consumer import (
    AccidenteReportadoConsumer,
)
from apps.despacho.services.confirmar_despacho_service import ConfirmarDespachoService


@pytest.mark.critical_path
class TestCadenaCriticaDespachoIntegration:
    def test_registro_to_confirmacion_completa(
        self, mock_pinot, mock_kafka, accidente_activo, unidad_con_estado_activa
    ):
        # Arrange
        consumer = AccidenteReportadoConsumer()

        # Act — O22
        asignacion = consumer.handle(
            {"idaccidente": accidente_activo, "estado": ESTADO_REPORTADO, "idusuario": 2}
        )
        assert asignacion["asignado"] is True

        # Act — O24
        confirmacion = ConfirmarDespachoService().confirmar(
            idnotificaciondespacho=asignacion["idnotificaciondespacho"],
            idunidademergencia=1,
            idusuario=6,
        )

        # Assert
        assert confirmacion["estado_caso"] == "ASIGNADO"
        assert confirmacion["estado_unidad"] == "En Misión"
