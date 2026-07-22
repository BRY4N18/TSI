import pytest


@pytest.mark.api
class TestModificarSLAConfigContract:
    def test_patch_when_admin_returns_201(self, api_client, auth_headers):
        # Act
        response = api_client.patch(
            "/api/v1/soporte/sla-config/1",
            {"tiemporespuestamax": 1800, "tiemporesolucionmax": 43200},
            format="json",
            **auth_headers,
        )

        # Assert
        assert response.status_code == 201
        assert response.json()["data"]["tiemporespuestamax"] == 1800

    def test_patch_when_not_found_returns_404(self, api_client, auth_headers):
        # Act
        response = api_client.patch(
            "/api/v1/soporte/sla-config/999",
            {"tiemporespuestamax": 1800, "tiemporesolucionmax": 43200},
            format="json",
            **auth_headers,
        )

        # Assert
        assert response.status_code == 404
