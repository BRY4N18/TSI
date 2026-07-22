import pytest

from apps.accidentes.domain_constants import ESTADO_REPORTADO
from apps.despacho.consumers.accidente_reportado_consumer import (
    AccidenteReportadoConsumer,
)
from core.repositories.accidentes.estado_accidente_repository import (
    EstadoAccidenteRepository,
)
from core.repositories.despacho.despacho_repository import DespachoRepository


@pytest.mark.critical_path
class TestAsignacionAutomaticaIntegration:
    def test_o22_consumer_creates_despacho_and_buscando_unidad(
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
        assert result["asignado"] is True
        despachos = DespachoRepository().list_by_accidente(accidente_activo)
        assert len(despachos) >= 1
        assert despachos[0]["activo"] is True
        estado = EstadoAccidenteRepository().get_current_estado(accidente_activo)
        assert estado in ("BUSCANDO_UNIDAD", "ASIGNADO")
