import pytest

from conftest import PINOT_STORE

pytestmark = pytest.mark.api


def test_alta_ok_sin_previa(api_client, proveedor_billing_auth_headers):
    PINOT_STORE["Fact_Suscripcion"].clear()
    response = api_client.post(
        "/api/v1/suscripciones",
        {"idplan": 1},
        format="json",
        HTTP_IDEMPOTENCY_KEY="alta-ok",
        **proveedor_billing_auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["data"]["estado"] == "Activa"
