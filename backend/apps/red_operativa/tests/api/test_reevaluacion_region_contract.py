import pytest


@pytest.mark.api
class TestReevaluacionRegionContract:
    URL = "/api/v1/red-operativa/regiones/1/reevaluacion"

    def test_post_when_produccion_a_en_alerta_returns_200(
        self, api_client, director_tecnologico_auth_headers, pinot_store
    ):
        # Arrange
        pinot_store["Dim_RegionOperativa"][0]["estadoregion"] = "Producción"

        # Act
        response = api_client.post(
            self.URL,
            {"estadoregion": "En_Alerta", "motivo": "Latencia"},
            format="json",
            **director_tecnologico_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["estadoregion"] == "En_Alerta"

    def test_post_when_produccion_a_despublicada_con_casos_activos_returns_200(
        self, api_client, director_tecnologico_auth_headers, pinot_store
    ):
        # Arrange
        pinot_store["Dim_RegionOperativa"][0]["estadoregion"] = "Producción"
        pinot_store["Fact_Accidente"].append({"idaccidente": "acc-1", "idcalle": 1, "activo": True})

        # Act
        response = api_client.post(
            self.URL,
            {"estadoregion": "Despublicada", "motivo": "Sin cobertura"},
            format="json",
            **director_tecnologico_auth_headers,
        )

        # Assert: no cancela casos activos, solo bloquea nuevos
        assert response.status_code == 200
        assert pinot_store["Fact_Accidente"][0]["activo"] is True

    def test_post_when_estado_origen_invalido_returns_409(
        self, api_client, director_tecnologico_auth_headers, pinot_store
    ):
        # Arrange
        pinot_store["Dim_RegionOperativa"][0]["estadoregion"] = "En_Validación"

        # Act
        response = api_client.post(
            self.URL,
            {"estadoregion": "En_Alerta", "motivo": "x"},
            format="json",
            **director_tecnologico_auth_headers,
        )

        # Assert
        assert response.status_code == 409

    def test_post_when_administrador_returns_403(self, api_client, admin_auth_headers, pinot_store):
        # Arrange
        pinot_store["Dim_RegionOperativa"][0]["estadoregion"] = "Producción"

        # Act
        response = api_client.post(
            self.URL,
            {"estadoregion": "En_Alerta", "motivo": "x"},
            format="json",
            **admin_auth_headers,
        )

        # Assert
        assert response.status_code == 403

    def test_post_when_director_tecnologico_returns_200(
        self, api_client, director_tecnologico_auth_headers, pinot_store
    ):
        # Arrange
        pinot_store["Dim_RegionOperativa"][0]["estadoregion"] = "Producción"

        # Act
        response = api_client.post(
            self.URL,
            {"estadoregion": "En_Alerta", "motivo": "x"},
            format="json",
            **director_tecnologico_auth_headers,
        )

        # Assert
        assert response.status_code == 200
