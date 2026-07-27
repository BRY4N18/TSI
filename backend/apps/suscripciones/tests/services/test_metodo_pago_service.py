import pytest

from apps.suscripciones.services.metodo_pago_service import MetodoPagoService
from apps.suscripciones.services.mora_suscripcion_service import MoraSuscripcionService
from conftest import PINOT_STORE
from core.repositories.suscripciones.factura_repository import FacturaRepository
from core.repositories.suscripciones.metodo_pago_repository import MetodoPagoRepository

pytestmark = pytest.mark.service


class TestMetodoPagoService:
    def test_registrar_tokeniza_sin_pan(self, mock_pinot, mock_kafka):
        # Arrange / Act
        result = MetodoPagoService().registrar(
            idcliente=1,
            tipo="tarjeta",
            datos_pasarela={"numero": "4111111111111111", "fechaexpiracion": "12/30"},
        )
        # Assert
        metodo = result["metodo"]
        assert metodo["ultimosdigitos"] == "1111"
        assert "4111111111111111" not in str(metodo)
        assert metodo["tokenpasarela"].startswith("tok_sim_")

    def test_rn021_regularizacion_si_suspendida(self, mock_pinot, mock_kafka):
        # Arrange
        PINOT_STORE["Fact_Suscripcion"][0]["estado"] = "Suspendida"
        MetodoPagoRepository().create(
            {
                "idcliente": 1,
                "tipo": "tarjeta",
                "tokenpasarela": "tok_old",
                "ultimosdigitos": "0000",
            }
        )
        FacturaRepository().create(
            {
                "id_cliente": 1,
                "id_suscripcion": 1,
                "idmetodopago": 1,
                "periodo": "2026-07",
                "monto_base": 49.0,
            }
        )
        fac = PINOT_STORE["Fact_Factura"][0]
        FacturaRepository().update(
            fac["id_factura"], {"estado_pago": "Fallida", "reintentos": 3}
        )
        # Act
        result = MetodoPagoService().registrar(
            idcliente=1,
            tipo="tarjeta",
            datos_pasarela={"numero": "4242424242424242"},
        )
        # Assert
        assert result["regularizacion_disparada"] is True
