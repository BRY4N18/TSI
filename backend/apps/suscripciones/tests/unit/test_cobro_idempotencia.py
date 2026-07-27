import pytest

from apps.suscripciones.services.cobro_service import CobroService
from apps.suscripciones.services.generacion_factura_service import GeneracionFacturaService
from conftest import PINOT_STORE
from core.repositories.suscripciones.metodo_pago_repository import MetodoPagoRepository

pytestmark = pytest.mark.unit


class TestCobroIdempotencia:
    def test_misma_clave_conceptual(self, mock_pinot, mock_kafka):
        MetodoPagoRepository().create(
            {
                "idcliente": 1,
                "tipo": "tarjeta",
                "tokenpasarela": "tok",
                "ultimosdigitos": "1",
            }
        )
        fac = GeneracionFacturaService().para_suscripcion(PINOT_STORE["Fact_Suscripcion"][0])
        first = CobroService().intentar(fac["id_factura"])
        second = CobroService().intentar(fac["id_factura"])
        assert first["estado_pago"] == second["estado_pago"] == "Pagada"
