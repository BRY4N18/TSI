import pytest


@pytest.mark.api
class TestParametrosDespachoContract:
    def test_get_when_director_returns_200(
        self, api_client, director_tecnologico_auth_headers
    ):
        # Act
        response = api_client.get(
            "/api/v1/despacho/parametros",
            **director_tecnologico_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["timeout_respuesta_seg"] == 90

    def test_patch_when_valid_returns_200(
        self, api_client, director_tecnologico_auth_headers
    ):
        # Act
        response = api_client.patch(
            "/api/v1/despacho/parametros",
            {"timeout_respuesta_seg": 75},
            format="json",
            **director_tecnologico_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["timeout_respuesta_seg"] == 75

    def test_patch_when_operador_returns_403(
        self, api_client, operador_despacho_auth_headers
    ):
        # Act
        response = api_client.patch(
            "/api/v1/despacho/parametros",
            {"timeout_respuesta_seg": 75},
            format="json",
            **operador_despacho_auth_headers,
        )

        # Assert
        assert response.status_code == 403
