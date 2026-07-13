import pytest


@pytest.mark.api
class TestListarUnidadesContract:
    def test_listar_when_admin_returns_200(self, api_client, admin_auth_headers):
        # Act
        response = api_client.get("/api/v1/unidades-emergencia", **admin_auth_headers)

        # Assert
        assert response.status_code == 200
        assert "items" in response.json()["data"]

    def test_listar_when_despacho_service_returns_200(
        self, api_client, despacho_service_auth_headers
    ):
        # Act
        response = api_client.get(
            "/api/v1/unidades-emergencia", **despacho_service_auth_headers
        )

        # Assert
        assert response.status_code == 200

    def test_listar_when_tecnico_returns_403(self, api_client, tecnico_auth_headers):
        # Act
        response = api_client.get("/api/v1/unidades-emergencia", **tecnico_auth_headers)

        # Assert
        assert response.status_code == 403
