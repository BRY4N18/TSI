import pytest
from unittest.mock import patch


@pytest.mark.api
class TestRegistroUnidadContract:
    def _valid_payload(self, **overrides):
        payload = {
            "idcondado": 1,
            "tipopropiedad": "Externa",
            "placa": "API-001",
            "contactoproveedor": "5551234",
            "unidademergencia": "Ambulancia Centro",
            "tipounidademergencia": "Ambulancia",
            "gmail": "api-unidad-001@test.com",
        }
        payload.update(overrides)
        return payload

    def test_post_unidad_when_proveedor_returns_201(self, api_client, proveedor_auth_headers):
        response = api_client.post(
            "/api/v1/red-operativa/unidades",
            self._valid_payload(),
            format="json",
            **proveedor_auth_headers,
        )
        assert response.status_code == 201
        body = response.json()
        assert body["data"]["placa"] == "API-001"
        assert body["data"]["activo"] is True
        assert "invitacion_enviada" in body["data"]
        assert "password" not in body["data"]
        assert "temp_password" not in str(body)

    def test_post_unidad_when_sin_gmail_returns_201_sin_usuario(
        self, api_client, proveedor_auth_headers
    ):
        # Arrange — SRS 3.5.1 / RF-O39.5-6: gmail es opcional en el alta individual.
        payload = self._valid_payload(placa="API-SIN-GMAIL")
        del payload["gmail"]

        # Act
        response = api_client.post(
            "/api/v1/red-operativa/unidades",
            payload,
            format="json",
            **proveedor_auth_headers,
        )

        # Assert
        assert response.status_code == 201
        body = response.json()["data"]
        assert body["usuario_creado"] is False
        assert body["invitacion_enviada"] is False
        assert body.get("idusuario") is None

    def test_post_unidad_when_placa_duplicada_returns_409(
        self, api_client, proveedor_auth_headers, mock_unidad_emergencia
    ):
        response = api_client.post(
            "/api/v1/red-operativa/unidades",
            self._valid_payload(placa=mock_unidad_emergencia["placa"], gmail="dup@test.com"),
            format="json",
            **proveedor_auth_headers,
        )
        assert response.status_code == 409

    def test_post_unidad_when_administrador_returns_403(self, api_client, admin_auth_headers):
        response = api_client.post(
            "/api/v1/red-operativa/unidades",
            self._valid_payload(),
            format="json",
            **admin_auth_headers,
        )
        assert response.status_code == 403

    def test_post_unidad_when_operador_returns_403(self, api_client, operador_auth_headers):
        response = api_client.post(
            "/api/v1/red-operativa/unidades",
            self._valid_payload(),
            format="json",
            **operador_auth_headers,
        )
        assert response.status_code == 403

    def test_post_unidad_when_unauthenticated_returns_401_or_403(self, api_client):
        response = api_client.post(
            "/api/v1/red-operativa/unidades",
            self._valid_payload(),
            format="json",
        )
        assert response.status_code in (401, 403)

    def test_list_after_create_includes_unidad_with_idcliente(
        self, api_client, proveedor_auth_headers
    ):
        create = api_client.post(
            "/api/v1/red-operativa/unidades",
            self._valid_payload(placa="API-OWN-1", gmail="own1@test.com"),
            format="json",
            **proveedor_auth_headers,
        )
        assert create.status_code == 201
        created_id = create.json()["data"]["idunidademergencia"]

        listed = api_client.get("/api/v1/red-operativa/unidades", **proveedor_auth_headers)
        assert listed.status_code == 200
        items = listed.json()["data"]["items"]
        match = next((u for u in items if u["idunidademergencia"] == created_id), None)
        assert match is not None
        assert int(match["idcliente"]) == 1

    @patch(
        "apps.cuentas_clientes.services.onboarding_notificacion_service."
        "OnboardingNotificacionService.notify_invitacion",
        return_value=False,
    )
    def test_post_unidad_when_smtp_fails_still_201(
        self, _mock_notify, api_client, proveedor_auth_headers
    ):
        response = api_client.post(
            "/api/v1/red-operativa/unidades",
            self._valid_payload(placa="API-SMTP", gmail="api-smtp@test.com"),
            format="json",
            **proveedor_auth_headers,
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["invitacion_enviada"] is False
        assert data.get("invitacion_error")
