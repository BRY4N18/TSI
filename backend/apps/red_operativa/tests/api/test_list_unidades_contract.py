import pytest


@pytest.mark.api
class TestListUnidadesContract:
    def test_get_unidades_when_proveedor_returns_200(
        self, api_client, proveedor_auth_headers, mock_unidad_emergencia
    ):
        response = api_client.get(
            "/api/v1/red-operativa/unidades",
            **proveedor_auth_headers,
        )

        assert response.status_code == 200
        body = response.json()
        items = body["data"]["items"]
        assert isinstance(items, list)
        assert any(
            u["idunidademergencia"] == mock_unidad_emergencia["idunidademergencia"] for u in items
        )

    def test_get_unidades_when_operador_returns_403(self, api_client, operador_auth_headers):
        response = api_client.get(
            "/api/v1/red-operativa/unidades",
            **operador_auth_headers,
        )
        assert response.status_code == 403

    def test_get_unidades_when_unauthenticated_returns_401(self, api_client):
        response = api_client.get("/api/v1/red-operativa/unidades")
        assert response.status_code == 401
