import pytest


@pytest.mark.api
class TestGetUnidadContract:
    def test_get_unidad_when_exists_returns_200(
        self, api_client, admin_auth_headers, mock_unidad_emergencia
    ):
        # Act
        response = api_client.get(
            f"/api/v1/red-operativa/unidades/{mock_unidad_emergencia['idunidademergencia']}",
            **admin_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["idunidademergencia"] == mock_unidad_emergencia["idunidademergencia"]

    def test_get_unidad_when_operador_returns_200(
        self, api_client, operador_auth_headers, mock_unidad_emergencia
    ):
        # Act
        response = api_client.get(
            f"/api/v1/red-operativa/unidades/{mock_unidad_emergencia['idunidademergencia']}",
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 200

    def test_get_unidad_when_not_exists_returns_404(self, api_client, admin_auth_headers):
        # Act
        response = api_client.get(
            "/api/v1/red-operativa/unidades/999999",
            **admin_auth_headers,
        )

        # Assert
        assert response.status_code == 404

    def test_get_unidad_when_unauthenticated_returns_403(self, api_client, mock_unidad_emergencia):
        # Act
        response = api_client.get(
            f"/api/v1/red-operativa/unidades/{mock_unidad_emergencia['idunidademergencia']}"
        )

        # Assert (JWTSessionAuthentication no implementa authenticate_header,
        # por lo que DRF degrada NotAuthenticated a 403 en todo el proyecto)
        assert response.status_code == 403
