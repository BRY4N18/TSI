import pytest


@pytest.mark.api
class TestRegistroUnidadContract:
    def _valid_payload(self, **overrides):
        payload = {
            "idcliente": 1,
            "idcondado": 1,
            "tipopropiedad": "Externa",
            "placa": "API-001",
            "contactoproveedor": "5551234",
            "unidademergencia": "Ambulancia Centro",
            "tipounidademergencia": "Ambulancia",
        }
        payload.update(overrides)
        return payload

    def test_post_unidad_when_administrador_returns_201(self, api_client, admin_auth_headers):
        # Act
        response = api_client.post(
            "/api/v1/red-operativa/unidades",
            self._valid_payload(),
            format="json",
            **admin_auth_headers,
        )

        # Assert
        assert response.status_code == 201
        body = response.json()
        assert body["data"]["placa"] == "API-001"
        assert body["data"]["activo"] is True

    def test_post_unidad_when_placa_duplicada_returns_409(
        self, api_client, admin_auth_headers, mock_unidad_emergencia
    ):
        # Act
        response = api_client.post(
            "/api/v1/red-operativa/unidades",
            self._valid_payload(placa=mock_unidad_emergencia["placa"]),
            format="json",
            **admin_auth_headers,
        )

        # Assert
        assert response.status_code == 409

    def test_post_unidad_when_operador_returns_403(self, api_client, operador_auth_headers):
        # Act
        response = api_client.post(
            "/api/v1/red-operativa/unidades",
            self._valid_payload(),
            format="json",
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 403

    def test_post_unidad_when_unauthenticated_returns_403(self, api_client):
        # Act
        response = api_client.post(
            "/api/v1/red-operativa/unidades",
            self._valid_payload(),
            format="json",
        )

        # Assert (JWTSessionAuthentication no implementa authenticate_header,
        # por lo que DRF degrada NotAuthenticated a 403 en todo el proyecto)
        assert response.status_code == 403
