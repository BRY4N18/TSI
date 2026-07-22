import pytest


@pytest.mark.api
class TestRechazoDefinitivoContract:
    URL = "/api/v1/red-operativa/regiones/1/rechazo-definitivo"

    def test_post_when_en_validacion_returns_200(
        self, api_client, admin_auth_headers, pinot_store
    ):
        # Arrange
        pinot_store["Dim_RegionOperativa"][0]["estadoregion"] = "En_Validación"

        # Act
        response = api_client.post(self.URL, {}, format="json", **admin_auth_headers)

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["activo"] is False

    def test_post_when_produccion_returns_409(self, api_client, admin_auth_headers, pinot_store):
        # Arrange
        pinot_store["Dim_RegionOperativa"][0]["estadoregion"] = "Producción"

        # Act
        response = api_client.post(self.URL, {}, format="json", **admin_auth_headers)

        # Assert
        assert response.status_code == 409

    def test_post_when_region_inexistente_returns_404(self, api_client, admin_auth_headers):
        # Act
        response = api_client.post(
            "/api/v1/red-operativa/regiones/999/rechazo-definitivo",
            {},
            format="json",
            **admin_auth_headers,
        )

        # Assert
        assert response.status_code == 404
