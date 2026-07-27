import pytest

pytestmark = pytest.mark.api


def test_aprobar_cambio_plan(api_client, proveedor_billing_auth_headers, admin_billing_auth_headers):
    # Downgrade Empresarial←seed as plan 3 first
    from conftest import PINOT_STORE

    PINOT_STORE["Fact_Suscripcion"][0]["idplan"] = 3
    crear = api_client.post(
        "/api/v1/suscripciones/solicitudes-cambio-plan",
        {"idplansolicitado": 1, "motivo": "costo"},
        format="json",
        HTTP_IDEMPOTENCY_KEY="cp-a",
        **proveedor_billing_auth_headers,
    )
    assert crear.status_code == 201
    assert crear.json()["data"]["estado"] == "Pendiente"
    sid = crear.json()["data"]["idsolicitud"]
    aprobar = api_client.post(
        f"/api/v1/suscripciones/solicitudes-cambio-plan/{sid}/aprobar",
        format="json",
        HTTP_IDEMPOTENCY_KEY="cp-ap",
        **admin_billing_auth_headers,
    )
    assert aprobar.status_code == 200
    assert aprobar.json()["data"]["estado"] == "Aprobada"
