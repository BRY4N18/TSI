import pytest

from core.repositories.suscripciones.factura_repository import FacturaRepository

pytestmark = pytest.mark.api


def test_factura_detalle(api_client, proveedor_billing_auth_headers):
    fac = FacturaRepository().create(
        {
            "id_cliente": 1,
            "id_suscripcion": 1,
            "periodo": "2026-07",
            "monto_base": 20.0,
        }
    )
    response = api_client.get(
        f"/api/v1/suscripciones/facturas/{fac['id_factura']}",
        **proveedor_billing_auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["numero_factura"].startswith("FAC-")
