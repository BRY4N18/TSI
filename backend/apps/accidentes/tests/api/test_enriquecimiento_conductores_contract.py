import pytest

CONDUCTOR_PAYLOAD = {
    "conductor": {
        "identificacion": "1717171717",
        "nombres": "Carlos",
        "apellidos": "Mora",
    },
    "idestadoconductor": 1,
    "vehiculo": {"tipovehiculo": "Camioneta"},
}


@pytest.mark.api
class TestEnriquecimientoConductoresContract:
    def test_post_and_get_when_tecnico_returns_201_and_200(
        self, api_client, tecnico_auth_headers, accidente_activo
    ):
        # Arrange / Act
        created = api_client.post(
            f"/api/v1/accidentes/{accidente_activo}/enriquecimiento/conductores",
            CONDUCTOR_PAYLOAD,
            format="json",
            **tecnico_auth_headers,
        )
        listed = api_client.get(
            f"/api/v1/accidentes/{accidente_activo}/enriquecimiento/conductores",
            **tecnico_auth_headers,
        )

        # Assert
        assert created.status_code == 201
        assert created.json()["data"]["conductor"]["identificacion"] == "1717171717"
        assert listed.status_code == 200
        assert len(listed.json()["data"]["items"]) == 1

    def test_patch_desactivar_when_valid_returns_200(
        self, api_client, tecnico_auth_headers, accidente_activo
    ):
        # Arrange
        created = api_client.post(
            f"/api/v1/accidentes/{accidente_activo}/enriquecimiento/conductores",
            {
                **CONDUCTOR_PAYLOAD,
                "conductor": {
                    **CONDUCTOR_PAYLOAD["conductor"],
                    "identificacion": "1818181818",
                },
            },
            format="json",
            **tecnico_auth_headers,
        )
        cid = created.json()["data"]["idconductoraccidente"]

        # Act
        response = api_client.patch(
            f"/api/v1/accidentes/{accidente_activo}/enriquecimiento/conductores/{cid}",
            {"activo": False},
            format="json",
            **tecnico_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["activo"] is False
