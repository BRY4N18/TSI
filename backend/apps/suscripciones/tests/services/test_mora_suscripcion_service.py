from unittest.mock import patch

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

    def test_regularizar_no_depende_de_releer_la_factura_reabierta(
        self, mock_pinot, mock_kafka
    ):
        """El cliente suspendido tiene que poder salir de la mora.

        `regularizar` reabre la factura a Pendiente y la cobra. Cuando el cobro la
        releía por id, Pinot devolvía todavía la versión `Fallida` durante 5-15 s y el
        cobro salía por la guarda de "no está Pendiente" sin intentar nada: la
        suscripción se quedaba Suspendida para siempre, que es exactamente lo que el
        SRS §3.3.1 quiere evitar al conservarle el acceso mínimo para regularizar.
        """
        # Arrange — Pinot no expone nada de lo que se escriba en esta operación
        self._seed_fallida()
        with patch.object(FacturaRepository, "find_by_id", return_value=None):
            # Act
            result = MoraSuscripcionService().regularizar(id_suscripcion=1)
        # Assert
        assert result["estado_pago"] == "Pagada"
        assert result["estado_suscripcion"] == "Activa"
