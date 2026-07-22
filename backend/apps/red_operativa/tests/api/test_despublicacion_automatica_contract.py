import pytest


@pytest.mark.api
class TestDespublicacionAutomaticaContract:
    URL = "/api/v1/red-operativa/regiones/1/despublicacion-automatica"

    def test_post_when_produccion_returns_200_despublicada(
        self, api_client, admin_auth_headers, pinot_store
    ):
        # Arrange
        pinot_store["Dim_RegionOperativa"][0]["estadoregion"] = "Producción"

        # Act
        response = api_client.post(self.URL, {}, format="json", **admin_auth_headers)

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["estadoregion"] == "Despublicada"

    def test_post_when_en_alerta_returns_200_despublicada(
        self, api_client, admin_auth_headers, pinot_store
    ):
        # Arrange
        pinot_store["Dim_RegionOperativa"][0]["estadoregion"] = "En_Alerta"

        # Act
        response = api_client.post(self.URL, {}, format="json", **admin_auth_headers)

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["estadoregion"] == "Despublicada"

    def test_post_when_region_inexistente_returns_404(self, api_client, admin_auth_headers):
        # Act
        response = api_client.post(
            "/api/v1/red-operativa/regiones/999/despublicacion-automatica",
            {},
            format="json",
            **admin_auth_headers,
        )

        # Assert
        assert response.status_code == 404

    def test_post_when_ya_en_validacion_returns_409(
        self, api_client, admin_auth_headers, pinot_store
    ):
        # Arrange
        pinot_store["Dim_RegionOperativa"][0]["estadoregion"] = "En_Validación"

        # Act
        response = api_client.post(self.URL, {}, format="json", **admin_auth_headers)

        # Assert
        assert response.status_code == 409

    def test_post_when_ya_despublicada_returns_409(
        self, api_client, admin_auth_headers, pinot_store
    ):
        # Arrange: segunda invocación sobre una región ya despublicada no debe
        # duplicar la transición ni el evento Kafka.
        pinot_store["Dim_RegionOperativa"][0]["estadoregion"] = "Despublicada"

        # Act
        response = api_client.post(self.URL, {}, format="json", **admin_auth_headers)

        # Assert
        assert response.status_code == 409
