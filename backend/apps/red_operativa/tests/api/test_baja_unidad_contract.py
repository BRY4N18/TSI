import pytest


@pytest.mark.api
class TestBajaUnidadContract:
    def test_post_baja_when_sin_despacho_activo_returns_200(
        self, api_client, proveedor_auth_headers, mock_unidad_emergencia
    ):
        # Act
        response = api_client.post(
            f"/api/v1/red-operativa/unidades/{mock_unidad_emergencia['idunidademergencia']}/baja",
            {"motivo": "Mantenimiento"},
            format="json",
            **proveedor_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["activo"] is False

    def test_post_baja_when_proveedor_despacho_activo_sin_forzar_returns_403(
        self, api_client, proveedor_auth_headers, mock_despacho_activo
    ):
        # Arrange — el proveedor nunca puede, con o sin forzar (ver test de arriba).
        # Act
        response = api_client.post(
            f"/api/v1/red-operativa/unidades/{mock_despacho_activo['idunidademergencia']}/baja",
            {"motivo": "Baja forzada"},
            format="json",
            **proveedor_auth_headers,
        )

        # Assert
        assert response.status_code == 403

    def test_post_baja_when_administrador_despacho_activo_sin_forzar_returns_409(
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

    def test_post_baja_when_proveedor_intenta_forzar_returns_403(
        self, api_client, proveedor_auth_headers, mock_despacho_activo
    ):
        # Arrange — SRS 3.5.1 / RF-O42.4: única excepción al autoservicio del
        # proveedor; solo un Administrador puede ejecutar la baja forzada.
        # Act
        response = api_client.post(
            f"/api/v1/red-operativa/unidades/{mock_despacho_activo['idunidademergencia']}/baja",
            {"motivo": "Baja forzada", "forzar": True},
            format="json",
            **proveedor_auth_headers,
        )

        # Assert
        assert response.status_code == 403

    def test_post_baja_when_administrador_fuerza_returns_200(
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
        assert response.json()["data"]["activo"] is False

    def test_post_baja_when_sin_motivo_returns_400(
        self, api_client, proveedor_auth_headers, mock_unidad_emergencia
    ):
        # Act
        response = api_client.post(
            f"/api/v1/red-operativa/unidades/{mock_unidad_emergencia['idunidademergencia']}/baja",
            {},
            format="json",
            **proveedor_auth_headers,
        )

        # Assert
        assert response.status_code == 400
