import pytest


@pytest.mark.api
class TestCatalogoRegistroContract:
    def test_tipos_reportado_returns_200(self, api_client, operador_auth_headers):
        response = api_client.get(
            "/api/v1/accidentes/tipos-reportado", **operador_auth_headers
        )
        assert response.status_code == 200
        ids = {item["id"] for item in response.json()["data"]}
        assert {1, 2, 3, 4}.issubset(ids)

    def test_referencias_estacion_returns_200(self, api_client, operador_auth_headers):
        response = api_client.get(
            "/api/v1/accidentes/referencias-estacion", **operador_auth_headers
        )
        assert response.status_code == 200
        items = response.json()["data"]
        assert any(item["id"] == 1 and "MEX" in item["nombre"] for item in items)

    def test_unidades_emergencia_when_unidad_returns_200(
        self, api_client, unidad_auth_headers
    ):
        response = api_client.get(
            "/api/v1/accidentes/unidades-emergencia", **unidad_auth_headers
        )
        assert response.status_code == 200
        ids = {item["id"] for item in response.json()["data"]}
        assert 1 in ids
        assert 2 in ids
