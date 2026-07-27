import pytest

pytestmark = pytest.mark.api


def test_list_metodos(api_client, proveedor_billing_auth_headers):
    response = api_client.get(
        "/api/v1/suscripciones/metodos-pago", **proveedor_billing_auth_headers
    )
    assert response.status_code == 200
