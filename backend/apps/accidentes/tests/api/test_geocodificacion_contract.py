import pytest


@pytest.mark.api
class TestGeocodificacionContract:
    def test_geocodificacion_when_valid_coords_returns_200(
        self, api_client, operador_auth_headers
    ):
        # Act
        response = api_client.get(
            "/api/v1/accidentes/geocodificacion-inversa",
            {"latitud": 19.43, "longitud": -99.13},
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["idcalle"] == 1
        assert body["data"]["en_cobertura_operativa"] is True

    def test_geocodificacion_when_missing_params_returns_400(
        self, api_client, operador_auth_headers
    ):
        # Act
        response = api_client.get(
            "/api/v1/accidentes/geocodificacion-inversa",
            {},
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 400
