import pytest


@pytest.mark.api
class TestReactivarUnidadContract:
    def test_post_reactivar_when_sin_conflicto_returns_200(
        self, api_client, admin_auth_headers, mock_unidad_emergencia
    ):
        # Arrange
        api_client.post(
            f"/api/v1/red-operativa/unidades/{mock_unidad_emergencia['idunidademergencia']}/baja",
            {"motivo": "Baja"},
            format="json",
            **admin_auth_headers,
        )

        # Act
        response = api_client.post(
            f"/api/v1/red-operativa/unidades/{mock_unidad_emergencia['idunidademergencia']}/reactivar",
            {},
            format="json",
            **admin_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["activo"] is True

    def test_post_reactivar_when_placa_duplicada_returns_409(
        self, api_client, admin_auth_headers, mock_unidad_emergencia
    ):
        # Arrange
        api_client.post(
            f"/api/v1/red-operativa/unidades/{mock_unidad_emergencia['idunidademergencia']}/baja",
            {"motivo": "Baja"},
            format="json",
            **admin_auth_headers,
        )
        api_client.post(
            "/api/v1/red-operativa/unidades",
            {
                "idcliente": 1,
                "idcondado": 1,
                "tipopropiedad": "Externa",
                "placa": mock_unidad_emergencia["placa"],
                "contactoproveedor": "555",
                "unidademergencia": "Otra unidad",
                "tipounidademergencia": "Patrulla",
            },
            format="json",
            **admin_auth_headers,
        )

        # Act
        response = api_client.post(
            f"/api/v1/red-operativa/unidades/{mock_unidad_emergencia['idunidademergencia']}/reactivar",
            {},
            format="json",
            **admin_auth_headers,
        )

        # Assert
        assert response.status_code == 409
