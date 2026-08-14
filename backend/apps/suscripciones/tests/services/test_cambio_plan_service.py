from unittest.mock import patch

import pytest

from apps.suscripciones.services.cambio_plan_service import CambioPlanError, CambioPlanService
from apps.suscripciones.services.cancelacion_service import CancelacionService
from apps.suscripciones.services.consulta_factura_service import ConsultaFacturaService
from apps.suscripciones.services.renovacion_service import RenovacionService
from conftest import PINOT_STORE
from core.repositories.suscripciones.factura_repository import FacturaRepository
from core.repositories.suscripciones.metodo_pago_repository import MetodoPagoRepository
from core.repositories.suscripciones.solicitud_cambio_plan_repository import (
    SolicitudCambioPlanRepository,
)

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

    def test_downgrade_aprobado_no_aplica_hasta_el_cierre_del_ciclo(
        self, mock_pinot, mock_kafka
    ):
        """Decisión #27: la reducción se programa, no se aplica al aprobarse.

        Aplicarla en el acto le retira al cliente un nivel de servicio que ya pagó
        hasta el fin del período, y deja la factura del ciclo en curso al precio del
        plan bajo — el prorrateo que el SRS §3.3.1 prohíbe expresamente.
        """
        # Arrange — forzar plan Empresarial
        PINOT_STORE["Fact_Suscripcion"][0]["idplan"] = 3
        # Act
        sol = CambioPlanService().solicitar(
            idcliente=1, idplansolicitado=1, motivo="bajar costo"
        )
        assert sol["estado"] == "Pendiente"
        approved = CambioPlanService().aprobar(idsolicitud=sol["idsolicitud"], idadmin=1)
        # Assert — resuelta, pero el plan vigente NO cambia todavía
        assert approved["estado"] == "Aprobada"
        sus = PINOT_STORE["Fact_Suscripcion"][0]
        assert sus["idplan"] == 3
        assert sus["idplan_programado"] == 1

    def test_downgrade_programado_se_aplica_al_renovar(self, mock_pinot, mock_kafka):
        # Arrange — reducción Empresarial(3) → Básico(1) ya aprobada y programada
        PINOT_STORE["Fact_Suscripcion"][0]["idplan"] = 3
        sol = CambioPlanService().solicitar(idcliente=1, idplansolicitado=1)
        CambioPlanService().aprobar(idsolicitud=sol["idsolicitud"], idadmin=1)
        # El ciclo vence
        PINOT_STORE["Fact_Suscripcion"][0]["fecha_fin"] = 1000
        # Act
        RenovacionService().ejecutar_batch()
        # Assert — ahora sí rige el plan nuevo, y la marca queda limpia
        sus = PINOT_STORE["Fact_Suscripcion"][0]
        assert sus["idplan"] == 1
        assert sus["idplan_programado"] == CambioPlanService.SIN_CAMBIO_PROGRAMADO
        assert sus["fecha_fin"] > 1000

    def test_upgrade_sincroniza_periodicidad_del_plan_nuevo(self, mock_pinot, mock_kafka):
        # Arrange — Profesional(2, Mensual) → Empresarial(3, Anual)
        PINOT_STORE["Fact_Suscripcion"][0]["idplan"] = 2
        PINOT_STORE["Fact_Suscripcion"][0]["periodicidad"] = "Mensual"
        # Act
        CambioPlanService().solicitar(idcliente=1, idplansolicitado=3, motivo="upgrade")
        # Assert: la periodicidad del plan nuevo rige desde ya (RN-SUSF-006: sin prorrateo del ciclo en curso).
        assert PINOT_STORE["Fact_Suscripcion"][0]["periodicidad"] == "Anual"

    def test_upgrade_auto_aprueba_aunque_pinot_aun_no_exponga_la_solicitud(
        self, mock_pinot, mock_kafka
    ):
        """La auto-aprobación no puede depender de releer lo recién escrito.

        En el entorno real la solicitud viaja por Kafka y Pinot tarda 5-15 s en
        exponerla, así que durante ese rato `find_by_id` devuelve vacío. Cuando la
        aprobación se apoyaba en esa relectura, todo upgrade moría con 404
        "Solicitud no pendiente" y dejaba la solicitud Pendiente para siempre.

        El doble en memoria refleja la escritura al instante y por eso no lo cazaba:
        aquí se fuerza el retardo anulando `find_by_id`.
        """
        # Arrange — Pinot todavía no ve nada de lo que se escriba en esta operación
        with patch.object(
            SolicitudCambioPlanRepository, "find_by_id", return_value=None
        ):
            # Act — Básico(1) → Profesional(2) es upgrade
            sol = CambioPlanService().solicitar(
                idcliente=1, idplansolicitado=2, motivo="upgrade"
            )
        # Assert
        assert sol["estado"] == "Aprobada"
        assert PINOT_STORE["Fact_Suscripcion"][0]["idplan"] == 2

    @pytest.mark.parametrize("estado", ["Suspendida", "Cancelada"])
    def test_no_se_cambia_de_plan_sobre_suscripcion_no_activa(
        self, estado, mock_pinot, mock_kafka
    ):
        """SRS §3.3.1: no se admite cambiar de plan sobre suspendida o cancelada.

        `find_activa_by_cliente` solo mira `activo`, y suspender deja `activo = True`
        cambiando únicamente `estado`. Sin esta guarda, un cliente suspendido por impago
        podía pedir una mejora de plan — y al ser mejora, se autoaprobaba y se aplicaba
        en el acto, subiéndose de plan mientras no paga.
        """
        # Arrange
        PINOT_STORE["Fact_Suscripcion"][0]["estado"] = estado
        # Act / Assert
        with pytest.raises(CambioPlanError) as exc:
            CambioPlanService().solicitar(idcliente=1, idplansolicitado=2)
        assert exc.value.http_status == 409
        assert PINOT_STORE["Fact_Suscripcion"][0]["idplan"] != 2

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


    def test_cada_ciclo_renovado_factura_su_propio_periodo(self, mock_pinot, mock_kafka):
        """Cada ciclo tiene que emitir su factura (SRS §3.3.1).

        `periodo_actual()` sale de `fecha_inicio`. Mientras la renovación solo movía
        `fecha_fin`, todo ciclo calculaba el MISMO período, la guarda de "no duplicar
        factura del mismo período" lo bloqueaba y la suscripción se facturaba **una sola
        vez en su vida**: se renovaba el servicio sin volver a cobrarlo nunca.
        """
        # Arrange — cliente con método de pago y un ciclo ya vencido
        MetodoPagoRepository().create(
            {
                "idcliente": 1,
                "tipo": "tarjeta",
                "tokenpasarela": "tok_1",
                "ultimosdigitos": "4242",
            }
        )
        sus = PINOT_STORE["Fact_Suscripcion"][0]
        inicio_original = sus["fecha_inicio"]
        sus["fecha_fin"] = 1000
        # Act
        RenovacionService().ejecutar_batch()
        # Assert — el ciclo nuevo arranca donde terminó el anterior
        assert PINOT_STORE["Fact_Suscripcion"][0]["fecha_inicio"] == 1000
        assert PINOT_STORE["Fact_Suscripcion"][0]["fecha_inicio"] != inicio_original
        periodos = [f["periodo"] for f in PINOT_STORE["Fact_Factura"]]
        assert len(periodos) == len(set(periodos)), "no debe duplicar período"

    def test_renueva_aunque_pinot_aun_no_exponga_la_factura(self, mock_pinot, mock_kafka):
        """La renovación cobra la factura que acaba de emitir, sin releerla.

        Contra el stack real el job entero reventaba con
        `ValueError: factura no encontrada`, porque Pinot tarda 5-15 s en exponer la
        factura recién publicada. El doble en memoria la refleja al instante y por eso
        no lo cazaba; aquí se fuerza el retardo anulando `find_by_id`.
        """
        # Arrange
        PINOT_STORE["Fact_Suscripcion"][0]["fecha_fin"] = 1000
        # Act
        with patch.object(FacturaRepository, "find_by_id", return_value=None):
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
