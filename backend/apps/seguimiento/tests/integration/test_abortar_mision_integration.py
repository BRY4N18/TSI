import pytest

from apps.despacho.consumers.despacho_abortado_consumer import DespachoAbortadoConsumer
from apps.seguimiento.services.abortar_mision_service import AbortarMisionService
from core.repositories.despacho.historial_despacho_repository import ESTADO_ABORTADO


@pytest.mark.critical_path
class TestAbortarMisionIntegration:
    def test_abortar_dispara_o36_reasignacion(
        self,
        mock_pinot,
        mock_kafka,
        accidente_activo,
        despacho_confirmado_unidad,
        unidad_con_estado_activa,
    ):
        # Arrange
        iddespacho = despacho_confirmado_unidad["iddespacho"]
        abortar = AbortarMisionService()

        # Act
        result = abortar.abortar(
            iddespacho=iddespacho,
            idunidademergencia=1,
            idusuario=6,
            motivo="Integración aborto",
        )
        consumer_result = DespachoAbortadoConsumer().handle(
            {
                "iddespacho": iddespacho,
                "idaccidente": accidente_activo,
                "idusuario": 6,
            }
        )

        # Assert
        assert result["estado_despacho"] == ESTADO_ABORTADO
        assert any("Abortado" in m["topic"] for m in mock_kafka)
        assert "reasignacion_iniciada" in consumer_result
