import pytest


@pytest.mark.api
class TestGetUnidadContract:
    def test_get_unidad_when_exists_returns_200(
        self, api_client, proveedor_auth_headers, mock_unidad_emergencia
    ):
        # Act
        response = api_client.get(
            f"/api/v1/red-operativa/unidades/{mock_unidad_emergencia['idunidademergencia']}",
            **proveedor_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["idunidademergencia"] == mock_unidad_emergencia["idunidademergencia"]

    def test_get_unidad_when_operador_returns_403(
        self, api_client, operador_auth_headers, mock_unidad_emergencia
    ):
        # Act
        response = api_client.get(
            f"/api/v1/red-operativa/unidades/{mock_unidad_emergencia['idunidademergencia']}",
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 403

    def test_get_unidad_when_not_exists_returns_404(self, api_client, proveedor_auth_headers):
        # Act
        response = api_client.get(
            "/api/v1/red-operativa/unidades/999999",
            **proveedor_auth_headers,
        )

        # Assert
        assert response.status_code == 404

    def test_get_unidad_when_unauthenticated_returns_403(self, api_client, mock_unidad_emergencia):
        # Act
        response = api_client.get(
            f"/api/v1/red-operativa/unidades/{mock_unidad_emergencia['idunidademergencia']}"
        )

        # Assert
        assert response.status_code == 403
