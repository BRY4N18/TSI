import pytest

from apps.suscripciones.services.mora_suscripcion_service import MoraSuscripcionService
from apps.suscripciones.services.pasarela.simulador_pasarela import SimuladorPasarela
from conftest import PINOT_STORE
from core.repositories.suscripciones.factura_repository import FacturaRepository
from core.repositories.suscripciones.metodo_pago_repository import MetodoPagoRepository

pytestmark = pytest.mark.service


class TestMoraSuscripcionService:
    def _seed_fallida(self):
        MetodoPagoRepository().create(
            {
                "idcliente": 1,
                "tipo": "tarjeta",
                "tokenpasarela": "tok",
                "ultimosdigitos": "1111",
            }
        )
        fac = FacturaRepository().create(
            {
                "id_cliente": 1,
                "id_suscripcion": 1,
                "idmetodopago": 1,
                "periodo": "2026-07",
                "monto_base": 49.0,
            }
        )
        FacturaRepository().update(
            fac["id_factura"], {"estado_pago": "Fallida", "reintentos": 3}
        )
        PINOT_STORE["Fact_Suscripcion"][0]["estado"] = "Suspendida"
        return fac

    def test_regularizar_exitoso(self, mock_pinot, mock_kafka):
        # Arrange
        self._seed_fallida()
        # Act
        result = MoraSuscripcionService().regularizar(id_suscripcion=1)
        # Assert
        assert result["estado_pago"] == "Pagada"
        assert result["estado_suscripcion"] == "Activa"
