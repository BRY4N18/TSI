import pytest


@pytest.mark.api
class TestCatalogosEnriquecimientoContract:
    def test_get_catalogos_when_tecnico_returns_200(
        self, api_client, tecnico_auth_headers
    ):
        # Arrange / Act
        periodos = api_client.get("/api/v1/catalogos/periodos-dias", **tecnico_auth_headers)
        climas = api_client.get("/api/v1/catalogos/estados-climas", **tecnico_auth_headers)
        fisicos = api_client.get(
            "/api/v1/catalogos/elementos-fisicos", **tecnico_auth_headers
        )
        estados = api_client.get(
            "/api/v1/catalogos/estados-conductor", **tecnico_auth_headers
        )

        # Assert
        assert periodos.status_code == 200
        assert climas.status_code == 200
        assert fisicos.status_code == 200
        assert estados.status_code == 200
        assert len(periodos.json()["data"]["items"]) >= 1
        assert len(climas.json()["data"]["items"]) >= 1
        assert len(fisicos.json()["data"]["items"]) >= 1
        assert len(estados.json()["data"]["items"]) >= 1
