import pytest

from conftest import PINOT_STORE
from core.repositories.suscripciones.factura_repository import FacturaRepository
from core.repositories.suscripciones.metodo_pago_repository import MetodoPagoRepository

pytestmark = pytest.mark.api


def test_reintentar_ok(api_client, proveedor_billing_auth_headers):
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
            "periodo": "2026-07",
            "monto_base": 49.0,
        }
    )
    FacturaRepository().update(fac["id_factura"], {"estado_pago": "Fallida", "reintentos": 3})
    PINOT_STORE["Fact_Suscripcion"][0]["estado"] = "Suspendida"
    response = api_client.post(
        "/api/v1/suscripciones/mia/reintentar-cobro",
        format="json",
        HTTP_IDEMPOTENCY_KEY="rc-ok",
        **proveedor_billing_auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["estado_suscripcion"] == "Activa"
