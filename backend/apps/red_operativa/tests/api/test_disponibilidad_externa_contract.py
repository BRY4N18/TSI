import pytest


@pytest.mark.api
class TestDisponibilidadExternaContract:
    def test_post_disponibilidad_when_operador_y_sin_despacho_returns_200(
        self, api_client, operador_auth_headers, mock_unidad_emergencia
    ):
        # Act
        response = api_client.post(
            f"/api/v1/red-operativa/unidades/{mock_unidad_emergencia['idunidademergencia']}/disponibilidad",
            {"estadonuevo": "Activa"},
            format="json",
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["estadonuevo"] == "Activa"

    def test_post_disponibilidad_when_activa_con_despacho_activo_returns_422(
        self, api_client, operador_auth_headers, mock_despacho_activo
    ):
        # Act
        response = api_client.post(
            f"/api/v1/red-operativa/unidades/{mock_despacho_activo['idunidademergencia']}/disponibilidad",
            {"estadonuevo": "Activa"},
            format="json",
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 422

    def test_post_disponibilidad_when_administrador_returns_403(
        self, api_client, admin_auth_headers, mock_unidad_emergencia
    ):
        # Act
        response = api_client.post(
            f"/api/v1/red-operativa/unidades/{mock_unidad_emergencia['idunidademergencia']}/disponibilidad",
            {"estadonuevo": "Activa"},
            format="json",
            **admin_auth_headers,
        )

        # Assert
        assert response.status_code == 403
