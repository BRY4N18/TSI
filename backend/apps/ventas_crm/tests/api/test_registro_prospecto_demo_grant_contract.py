import pytest

pytestmark = pytest.mark.api


def test_registro_devuelve_demo_grant(api_client, mock_kafka):
    # Arrange / Act
    r = api_client.post(
        "/api/v1/ventas-crm/prospectos",
        {
            "nombres": "Laura",
            "apellidos": "Comercial",
            "gmail": "laura.grant@example.com",
            "empresa": "Acme",
            "tipo_organizacion": "Privado",
            "cargo": "Compras",
            "telefono": "3000000000",
            "como_nos_conocio": "web",
        },
        format="json",
    )
    # Assert
    assert r.status_code == 201
    assert r.data["data"]["demo_grant"]
