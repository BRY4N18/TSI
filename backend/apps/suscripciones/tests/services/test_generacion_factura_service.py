import pytest

from apps.suscripciones.services.cobro_service import CobroService
from apps.suscripciones.services.generacion_factura_service import GeneracionFacturaService
from conftest import PINOT_STORE
from core.repositories.suscripciones.metodo_pago_repository import MetodoPagoRepository

pytestmark = pytest.mark.service


class TestGeneracionFacturaService:
    def test_sin_metodo_no_crea(self, mock_pinot, mock_kafka):
        # Arrange
        sus = PINOT_STORE["Fact_Suscripcion"][0]
        # Act
        fac = GeneracionFacturaService().para_suscripcion(sus)
        # Assert
        assert fac is None

    def test_crea_con_metodo(self, mock_pinot, mock_kafka):
        # Arrange
        MetodoPagoRepository().create(
            {
                "idcliente": 1,
                "tipo": "tarjeta",
                "tokenpasarela": "tok",
                "ultimosdigitos": "1111",
            }
        )
        sus = PINOT_STORE["Fact_Suscripcion"][0]
        # Act
        fac = GeneracionFacturaService().para_suscripcion(sus)
        # Assert
        assert fac["estado_pago"] == "Pendiente"
        assert fac["impuestos"] == 0.0


class TestCobroService:
    def test_cobro_exitoso(self, mock_pinot, mock_kafka):
        # Arrange
        MetodoPagoRepository().create(
            {
                "idcliente": 1,
                "tipo": "tarjeta",
                "tokenpasarela": "tok",
                "ultimosdigitos": "1111",
            }
        )
        fac = GeneracionFacturaService().para_suscripcion(PINOT_STORE["Fact_Suscripcion"][0])
        # Act
        updated = CobroService().intentar(fac["id_factura"])
        # Assert
        assert updated["estado_pago"] == "Pagada"

    def test_tres_fallos_suspende(self, mock_pinot, mock_kafka):
        # Arrange
        MetodoPagoRepository().create(
            {
                "idcliente": 1,
                "tipo": "tarjeta",
                "tokenpasarela": "tok",
                "ultimosdigitos": "1111",
            }
        )
        fac = GeneracionFacturaService().para_suscripcion(PINOT_STORE["Fact_Suscripcion"][0])
        svc = CobroService()
        # Act
        for _ in range(3):
            updated = svc.intentar(fac["id_factura"], force_fail=True)
        # Assert
        assert updated["estado_pago"] == "Fallida"
        assert PINOT_STORE["Fact_Suscripcion"][0]["estado"] == "Suspendida"
