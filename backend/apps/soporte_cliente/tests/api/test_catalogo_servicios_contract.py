import pytest


@pytest.mark.api
class TestCatalogoServiciosContract:
    def test_listar_servicios_returns_200(self, api_client, cliente_auth_headers):
        response = api_client.get("/api/v1/soporte/servicios", **cliente_auth_headers)
        assert response.status_code == 200
        ids = {item["id"] for item in response.json()["data"]}
        assert {1, 2, 3}.issubset(ids)
