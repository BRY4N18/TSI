from unittest.mock import patch

import pytest

from apps.suscripciones.services.alta_suscripcion_service import (
    AltaSuscripcionError,
    AltaSuscripcionService,
)
from conftest import PINOT_STORE
from core.repositories.suscripciones.factura_repository import FacturaRepository
from core.repositories.suscripciones.metodo_pago_repository import MetodoPagoRepository

pytestmark = pytest.mark.service


class TestAltaSuscripcionService:
    def test_conflict_si_ya_activa(self, mock_pinot, mock_kafka):
        # Arrange / Act / Assert
        with pytest.raises(AltaSuscripcionError) as exc:
            AltaSuscripcionService().ejecutar(idcliente=1, idplan=2)
        assert exc.value.http_status == 409

    def test_alta_cliente_sin_suscripcion(self, mock_pinot, mock_kafka):
        # Arrange
        PINOT_STORE["Fact_Suscripcion"].clear()
        PINOT_STORE["Dim_Cliente"].append(
            {
                "idcliente": 99,
                "nombre": "Nuevo",
                "estado": "Activo",
                "admin_local_id": 99,
                "plan_suscripcion": None,
            }
        )
        # Act
        result = AltaSuscripcionService().ejecutar(idcliente=99, idplan=1)
        # Assert
        assert result["suscripcion"]["estado"] == "Activa"
        assert result["suscripcion"]["idcliente"] == 99
        assert result["suscripcion"]["periodicidad"] == "Mensual"

    def test_alta_con_metodo_de_pago_no_relee_la_factura_recien_emitida(
        self, mock_pinot, mock_kafka
    ):
        """Contratar teniendo método de pago emite la factura y la cobra en el acto.

        Cobrarla por id obligaba a releerla de Pinot, que no la expone hasta 5-15 s
        después: el alta reventaba con `ValueError: factura no encontrada` y respondía
        500 a todo cliente que ya tuviera método registrado.
        """
        # Arrange
        PINOT_STORE["Fact_Suscripcion"].clear()
        PINOT_STORE["Dim_Cliente"].append(
            {
                "idcliente": 97,
                "nombre": "Cliente Con Tarjeta",
                "estado": "Activo",
                "admin_local_id": 97,
                "plan_suscripcion": None,
            }
        )
        MetodoPagoRepository().create(
            {
                "idcliente": 97,
                "tipo": "tarjeta",
                "tokenpasarela": "tok_97",
                "ultimosdigitos": "4242",
            }
        )
        # Act — Pinot todavía no expone nada escrito en esta operación
        with patch.object(FacturaRepository, "find_by_id", return_value=None):
            result = AltaSuscripcionService().ejecutar(idcliente=97, idplan=1)
        # Assert
        assert result["suscripcion"]["estado"] == "Activa"
        assert result["factura"]["id_factura"]

    def test_alta_con_plan_anual_fija_ciclo_de_un_ano(self, mock_pinot, mock_kafka):
        # Arrange: idplan=3 (Empresarial) esta sembrado como periodicidad="Anual".
        PINOT_STORE["Fact_Suscripcion"].clear()
        PINOT_STORE["Dim_Cliente"].append(
            {
                "idcliente": 98,
                "nombre": "Cliente Anual",
                "estado": "Activo",
                "admin_local_id": 98,
                "plan_suscripcion": None,
            }
        )
        # Act
        result = AltaSuscripcionService().ejecutar(idcliente=98, idplan=3)
        # Assert: fecha_fin ~ 1 año despues de fecha_inicio, no 1 mes (SRS §3.3.1 "periodicidad").
        sus = result["suscripcion"]
        assert sus["periodicidad"] == "Anual"
        duracion_dias = (sus["fecha_fin"] - sus["fecha_inicio"]) / 86_400_000
        assert 360 <= duracion_dias <= 366
