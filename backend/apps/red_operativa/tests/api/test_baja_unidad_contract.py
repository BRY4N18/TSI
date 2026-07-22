import pytest


@pytest.mark.api
class TestBajaUnidadContract:
    def test_post_baja_when_sin_despacho_activo_returns_200(
        self, api_client, admin_auth_headers, mock_unidad_emergencia
    ):
        # Act
        response = api_client.post(
            f"/api/v1/red-operativa/unidades/{mock_unidad_emergencia['idunidademergencia']}/baja",
            {"motivo": "Mantenimiento"},
            format="json",
            **admin_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["activo"] is False

    def test_post_baja_when_despacho_activo_sin_forzar_returns_409(
        self, api_client, admin_auth_headers, mock_despacho_activo
    ):
        # Act
        response = api_client.post(
            f"/api/v1/red-operativa/unidades/{mock_despacho_activo['idunidademergencia']}/baja",
            {"motivo": "Baja forzada"},
            format="json",
            **admin_auth_headers,
        )

        # Assert
        assert response.status_code == 409

    def test_post_baja_when_forzada_returns_200(
        self, api_client, admin_auth_headers, mock_despacho_activo
    ):
        # Act
        response = api_client.post(
            f"/api/v1/red-operativa/unidades/{mock_despacho_activo['idunidademergencia']}/baja",
            {"motivo": "Baja forzada", "forzar": True},
            format="json",
            **admin_auth_headers,
        )

        # Assert
        assert response.status_code == 200

    def test_post_baja_when_sin_motivo_returns_400(
        self, api_client, admin_auth_headers, mock_unidad_emergencia
    ):
        # Act
        response = api_client.post(
            f"/api/v1/red-operativa/unidades/{mock_unidad_emergencia['idunidademergencia']}/baja",
            {},
            format="json",
            **admin_auth_headers,
        )

        # Assert
        assert response.status_code == 400
