import pytest

IMPLICADO_PAYLOAD = {
    "tipoimplicado": "Peaton",
    "estadoimplicado": "Ileso",
    "genero": "F",
    "edad": 34,
}


@pytest.mark.api
class TestEnriquecimientoImplicadosContract:
    def test_post_and_get_when_tecnico_returns_201_and_200(
        self, api_client, tecnico_auth_headers, accidente_activo
    ):
        # Arrange / Act
        created = api_client.post(
            f"/api/v1/accidentes/{accidente_activo}/enriquecimiento/implicados",
            IMPLICADO_PAYLOAD,
            format="json",
            **tecnico_auth_headers,
        )
        listed = api_client.get(
            f"/api/v1/accidentes/{accidente_activo}/enriquecimiento/implicados",
            **tecnico_auth_headers,
        )
        consult = api_client.get(
            f"/api/v1/accidentes/{accidente_activo}/enriquecimiento",
            **tecnico_auth_headers,
        )

        # Assert
        assert created.status_code == 201
        data = created.json()["data"]
        assert data["tipoimplicado"] == "Peaton"
        assert data["estadoimplicado"] == "Ileso"
        assert data["edad"] == 34
        assert "identificacion" not in data
        assert "nombres" not in data
        assert listed.status_code == 200
        assert len(listed.json()["data"]["items"]) == 1
        assert consult.status_code == 200
        assert len(consult.json()["data"]["implicados"]) == 1

    def test_post_when_missing_estado_returns_400(
        self, api_client, tecnico_auth_headers, accidente_activo
    ):
        response = api_client.post(
            f"/api/v1/accidentes/{accidente_activo}/enriquecimiento/implicados",
            {"tipoimplicado": "Peaton"},
            format="json",
            **tecnico_auth_headers,
        )
        assert response.status_code == 400

    def test_patch_desactivar_when_valid_returns_200(
        self, api_client, tecnico_auth_headers, accidente_activo
    ):
        # Arrange
        created = api_client.post(
            f"/api/v1/accidentes/{accidente_activo}/enriquecimiento/implicados",
            {
                "tipoimplicado": "Testigo",
                "estadoimplicado": "Desconocido",
            },
            format="json",
            **tecnico_auth_headers,
        )
        iid = created.json()["data"]["idimplicado"]

        # Act
        response = api_client.patch(
            f"/api/v1/accidentes/{accidente_activo}/enriquecimiento/implicados/{iid}",
            {"activo": False},
            format="json",
            **tecnico_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["activo"] is False
