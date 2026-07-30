import pytest


@pytest.mark.api
class TestEnriquecimientoClimaContract:
    def test_put_clima_when_tecnico_returns_200(
        self, api_client, tecnico_auth_headers, accidente_activo
    ):
        # Arrange / Act
        response = api_client.put(
            f"/api/v1/accidentes/{accidente_activo}/enriquecimiento/clima",
            {"idperiododia": 1, "idestadoclima": 2},
            format="json",
            **tecnico_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["idperiododia"] == 1
        assert data["idestadoclima"] == 2
        assert data["activo"] is True

    def test_put_clima_when_admin_returns_403(
        self, api_client, admin_auth_headers, accidente_activo
    ):
        # Arrange / Act
        response = api_client.put(
            f"/api/v1/accidentes/{accidente_activo}/enriquecimiento/clima",
            {"idperiododia": 1},
            format="json",
            **admin_auth_headers,
        )

        # Assert
        assert response.status_code == 403
