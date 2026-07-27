import pytest

from apps.suscripciones.services.cambio_plan_service import CambioPlanError, CambioPlanService
from apps.suscripciones.services.cancelacion_service import CancelacionService
from apps.suscripciones.services.consulta_factura_service import ConsultaFacturaService
from apps.suscripciones.services.renovacion_service import RenovacionService
from conftest import PINOT_STORE
from core.repositories.suscripciones.factura_repository import FacturaRepository

pytestmark = pytest.mark.service


class TestCambioPlanService:
    def test_upgrade_auto_aprueba(self, mock_pinot, mock_kafka):
        # Arrange / Act — Básico(1) → Profesional(2)
        sol = CambioPlanService().solicitar(
            idcliente=1, idplansolicitado=2, motivo="upgrade"
        )
        # Assert
        assert sol["estado"] == "Aprobada"
        assert PINOT_STORE["Fact_Suscripcion"][0]["idplan"] == 2

    def test_downgrade_queda_pendiente(self, mock_pinot, mock_kafka):
        # Arrange — forzar plan Empresarial
        PINOT_STORE["Fact_Suscripcion"][0]["idplan"] = 3
        # Act
        sol = CambioPlanService().solicitar(
            idcliente=1, idplansolicitado=1, motivo="bajar costo"
        )
        # Assert
        assert sol["estado"] == "Pendiente"
        approved = CambioPlanService().aprobar(idsolicitud=sol["idsolicitud"], idadmin=1)
        assert approved["estado"] == "Aprobada"
        assert PINOT_STORE["Fact_Suscripcion"][0]["idplan"] == 1

    def test_conflict_pendiente(self, mock_pinot, mock_kafka):
        PINOT_STORE["Fact_Suscripcion"][0]["idplan"] = 3
        CambioPlanService().solicitar(idcliente=1, idplansolicitado=2)
        with pytest.raises(CambioPlanError) as exc:
            CambioPlanService().solicitar(idcliente=1, idplansolicitado=1)
        assert exc.value.http_status == 409


class TestCancelacionService:
    def test_cancelar(self, mock_pinot, mock_kafka):
        # Act
        sus = CancelacionService().cancelar(
            idcliente=1, motivocancelacion="ya no necesito"
        )
        # Assert
        assert sus["estado"] == "Cancelada"
        assert sus["renovacionautomatica"] is False


class TestRenovacionService:
    def test_renueva_si_fecha_fin_pasada(self, mock_pinot, mock_kafka):
        # Arrange
        PINOT_STORE["Fact_Suscripcion"][0]["fecha_fin"] = 1000  # epoch ms past
        # Act
        out = RenovacionService().ejecutar_batch()
        # Assert
        assert len(out) == 1
        assert PINOT_STORE["Fact_Suscripcion"][0]["fecha_fin"] > 1000


class TestConsultaFacturaService:
    def test_listar_vacio(self, mock_pinot, mock_kafka):
        assert ConsultaFacturaService().listar(1) == []

    def test_listar_con_factura(self, mock_pinot, mock_kafka):
        FacturaRepository().create(
            {
                "id_cliente": 1,
                "id_suscripcion": 1,
                "periodo": "2026-07",
                "monto_base": 10.0,
            }
        )
        assert len(ConsultaFacturaService().listar(1)) == 1
