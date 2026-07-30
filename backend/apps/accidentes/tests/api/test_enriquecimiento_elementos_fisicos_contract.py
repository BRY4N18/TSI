import pytest


@pytest.mark.api
class TestEnriquecimientoElementosFisicosContract:
    def test_post_and_list_when_tecnico_returns_201_and_200(
        self, api_client, tecnico_auth_headers, accidente_activo
    ):
        # Arrange / Act
        created = api_client.post(
            f"/api/v1/accidentes/{accidente_activo}/enriquecimiento/elementos-fisicos",
            {"idelementofisico": 1},
            format="json",
            **tecnico_auth_headers,
        )
        listed = api_client.get(
            f"/api/v1/accidentes/{accidente_activo}/enriquecimiento/elementos-fisicos",
            **tecnico_auth_headers,
        )

        # Assert
        assert created.status_code == 201
        assert created.json()["data"]["elementofisico"] == "Semáforo"
        assert listed.status_code == 200
        assert len(listed.json()["data"]["items"]) == 1

    def test_patch_desactivar_when_valid_returns_200(
        self, api_client, tecnico_auth_headers, accidente_activo
    ):
        # Arrange
        created = api_client.post(
            f"/api/v1/accidentes/{accidente_activo}/enriquecimiento/elementos-fisicos",
            {"idelementofisico": 2},
            format="json",
            **tecnico_auth_headers,
        )
        eid = created.json()["data"]["idelementosfisicosaccidente"]

        # Act
        response = api_client.patch(
            f"/api/v1/accidentes/{accidente_activo}/enriquecimiento/elementos-fisicos/{eid}",
            {"activo": False},
            format="json",
            **tecnico_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["activo"] is False
