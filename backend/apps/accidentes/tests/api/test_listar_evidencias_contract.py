import pytest


@pytest.mark.api
class TestListarEvidenciasContract:
    def test_listar_when_tecnico_returns_200(
        self, api_client, tecnico_auth_headers, accidente_activo
    ):
        # Act
        response = api_client.get(
            f"/api/v1/accidentes/{accidente_activo}/evidencias",
            **tecnico_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert "items" in body["data"]
        assert "meta" in body

    def test_listar_when_cliente_returns_403(
        self, api_client, cliente_auth_headers, accidente_activo
    ):
        # Act
        response = api_client.get(
            f"/api/v1/accidentes/{accidente_activo}/evidencias",
            **cliente_auth_headers,
        )

        # Assert
        assert response.status_code == 403
