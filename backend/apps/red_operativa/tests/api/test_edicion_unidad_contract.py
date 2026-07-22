import pytest


@pytest.mark.api
class TestEdicionUnidadContract:
    def test_patch_unidad_when_campo_no_critico_returns_200(
        self, api_client, admin_auth_headers, mock_unidad_emergencia
    ):
        # Act
        response = api_client.patch(
            f"/api/v1/red-operativa/unidades/{mock_unidad_emergencia['idunidademergencia']}",
            {"capacidad": "10"},
            format="json",
            **admin_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert "capacidad" in response.json()["data"]["campos_modificados"]

    def test_patch_unidad_when_critico_con_despacho_activo_sin_confirmar_returns_409(
        self, api_client, admin_auth_headers, mock_despacho_activo
    ):
        # Act
        response = api_client.patch(
            f"/api/v1/red-operativa/unidades/{mock_despacho_activo['idunidademergencia']}",
            {"tipounidademergencia": "Patrulla"},
            format="json",
            **admin_auth_headers,
        )

        # Assert
        assert response.status_code == 409

    def test_patch_unidad_when_critico_confirmado_returns_200(
        self, api_client, admin_auth_headers, mock_despacho_activo
    ):
        # Act
        response = api_client.patch(
            f"/api/v1/red-operativa/unidades/{mock_despacho_activo['idunidademergencia']}"
            "?confirmar_edicion_critica=true",
            {"tipounidademergencia": "Patrulla"},
            format="json",
            **admin_auth_headers,
        )

        # Assert
        assert response.status_code == 200

    def test_patch_unidad_when_operador_returns_403(
        self, api_client, operador_auth_headers, mock_unidad_emergencia
    ):
        # Act
        response = api_client.patch(
            f"/api/v1/red-operativa/unidades/{mock_unidad_emergencia['idunidademergencia']}",
            {"capacidad": "10"},
            format="json",
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 403
