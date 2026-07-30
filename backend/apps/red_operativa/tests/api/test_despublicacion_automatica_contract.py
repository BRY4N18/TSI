import pytest


def _sin_cobertura(pinot_store):
    for u in pinot_store["Dim_UnidadEmergencia"]:
        if u.get("idcondado") in (1, 2):
            u["activo"] = False


@pytest.mark.api
class TestDespublicacionAutomaticaContract:
    URL = "/api/v1/red-operativa/regiones/1/despublicacion-automatica"

    def test_post_when_produccion_sin_cobertura_returns_200(
        self, api_client, admin_auth_headers, pinot_store
    ):
        _sin_cobertura(pinot_store)
        pinot_store["Dim_RegionOperativa"][0]["estadoregion"] = "Producción"

        response = api_client.post(self.URL, {}, format="json", **admin_auth_headers)

        assert response.status_code == 200
        assert response.json()["data"]["estadoregion"] == "Despublicada"

    def test_post_when_hay_cobertura_returns_409(
        self, api_client, admin_auth_headers, pinot_store
    ):
        pinot_store["Dim_RegionOperativa"][0]["estadoregion"] = "Producción"

        response = api_client.post(self.URL, {}, format="json", **admin_auth_headers)

        assert response.status_code == 409

    def test_post_when_en_alerta_sin_cobertura_returns_200(
        self, api_client, admin_auth_headers, pinot_store
    ):
        _sin_cobertura(pinot_store)
        pinot_store["Dim_RegionOperativa"][0]["estadoregion"] = "En_Alerta"

        response = api_client.post(self.URL, {}, format="json", **admin_auth_headers)

        assert response.status_code == 200
        assert response.json()["data"]["estadoregion"] == "Despublicada"

    def test_post_when_region_inexistente_returns_404(self, api_client, admin_auth_headers):
        response = api_client.post(
            "/api/v1/red-operativa/regiones/999/despublicacion-automatica",
            {},
            format="json",
            **admin_auth_headers,
        )
        assert response.status_code == 404

    def test_post_when_ya_en_validacion_returns_409(
        self, api_client, admin_auth_headers, pinot_store
    ):
        pinot_store["Dim_RegionOperativa"][0]["estadoregion"] = "En_Validación"

        response = api_client.post(self.URL, {}, format="json", **admin_auth_headers)

        assert response.status_code == 409

    def test_post_when_ya_despublicada_returns_409(
        self, api_client, admin_auth_headers, pinot_store
    ):
        pinot_store["Dim_RegionOperativa"][0]["estadoregion"] = "Despublicada"

        response = api_client.post(self.URL, {}, format="json", **admin_auth_headers)

        assert response.status_code == 409
