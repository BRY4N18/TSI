import pytest


@pytest.mark.api
class TestBajaCuentaContract:
    def test_baja_when_admin_returns_envelope(self, api_client, auth_headers):
        # Act
        response = api_client.post(
            "/api/v1/cuentas-clientes/1/baja",
            {"motivo": "Prueba"},
            format="json",
            **auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["estado"] == "Dado de baja"

    def test_baja_when_not_admin_returns_403(self, api_client, cliente_auth_headers):
        # Act
        response = api_client.post(
            "/api/v1/cuentas-clientes/1/baja",
            {},
            format="json",
            **cliente_auth_headers,
        )

        # Assert
        assert response.status_code == 403
