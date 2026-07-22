import pytest


@pytest.mark.api
class TestHistorialValidacionContract:
    def test_get_when_historial_existe_returns_ordenado(
        self, api_client, admin_auth_headers
    ):
        # Arrange
        api_client.post(
            "/api/v1/red-operativa/regiones/validaciones",
            {"idregionoperativa": 1, "resultado": "Rechazada", "motivo": "a"},
            format="json",
            **admin_auth_headers,
        )

        # Act
        response = api_client.get(
            "/api/v1/red-operativa/regiones/1/validaciones", **admin_auth_headers
        )

        # Assert
        assert response.status_code == 200
        assert len(response.json()["data"]) == 1

    def test_get_when_region_inexistente_returns_404(self, api_client, admin_auth_headers):
        # Act
        response = api_client.get(
            "/api/v1/red-operativa/regiones/999/validaciones", **admin_auth_headers
        )

        # Assert
        assert response.status_code == 404

    def test_get_when_unauthenticated_returns_403(self, api_client):
        # Act
        response = api_client.get("/api/v1/red-operativa/regiones/1/validaciones")

        # Assert
        assert response.status_code == 403
