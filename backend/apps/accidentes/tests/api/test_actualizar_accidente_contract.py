import pytest


@pytest.mark.api
class TestActualizarAccidenteContract:
    def test_patch_when_increment_numvehiculos_returns_200(
        self, api_client, operador_auth_headers, seed_accidente
    ):
        # Arrange
        aid = seed_accidente(idaccidente="ACC-PATCH-1", numvehiculos=1)

        # Act
        response = api_client.patch(
            f"/api/v1/accidentes/{aid}",
            {"numvehiculos": 3},
            format="json",
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert "numvehiculos" in response.json()["data"]["campos_modificados"]

    def test_patch_when_decrement_metric_returns_422(
        self, api_client, operador_auth_headers, seed_accidente
    ):
        # Arrange
        aid = seed_accidente(idaccidente="ACC-PATCH-2", numvehiculos=5)

        # Act
        response = api_client.patch(
            f"/api/v1/accidentes/{aid}",
            {"numvehiculos": 2},
            format="json",
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 422
