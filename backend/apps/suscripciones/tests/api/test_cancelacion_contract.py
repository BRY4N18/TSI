import pytest

pytestmark = pytest.mark.api


def test_cancelar_requiere_motivo(api_client, proveedor_billing_auth_headers):
    response = api_client.post(
        "/api/v1/suscripciones/mia/cancelar",
        {"motivocancelacion": ""},
        format="json",
        HTTP_IDEMPOTENCY_KEY="can-bad",
        **proveedor_billing_auth_headers,
    )
    assert response.status_code == 400
