import pytest


@pytest.mark.api
class TestConsultarEnriquecimientoContract:
    def test_get_enriquecimiento_when_tecnico_returns_200(
        self, api_client, tecnico_auth_headers, accidente_activo
    ):
        # Arrange
        api_client.put(
            f"/api/v1/accidentes/{accidente_activo}/enriquecimiento/clima",
            {"idperiododia": 2, "idestadoclima": 1},
            format="json",
            **tecnico_auth_headers,
        )

        # Act
        response = api_client.get(
            f"/api/v1/accidentes/{accidente_activo}/enriquecimiento",
            **tecnico_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["idaccidente"] == accidente_activo
        assert data["clima"]["idperiododia"] == 2
        assert "elementos_fisicos" in data
        assert "conductores" in data
