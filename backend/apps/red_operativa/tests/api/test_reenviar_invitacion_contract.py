import pytest
from unittest.mock import patch


@pytest.mark.api
class TestReenviarInvitacionUnidadContract:
    def _create_unidad(self, api_client, proveedor_auth_headers, placa="REENV-001"):
        response = api_client.post(
            "/api/v1/red-operativa/unidades",
            {
                "idcondado": 1,
                "tipopropiedad": "Externa",
                "placa": placa,
                "contactoproveedor": "5551234",
                "unidademergencia": "Unidad Reenvio",
                "tipounidademergencia": "Ambulancia",
                "gmail": f"{placa.lower()}@test.com",
            },
            format="json",
            **proveedor_auth_headers,
        )
        assert response.status_code == 201
        return response.json()["data"]

    def test_reenviar_when_proveedor_returns_200(self, api_client, proveedor_auth_headers):
        created = self._create_unidad(api_client, proveedor_auth_headers)
        response = api_client.post(
            f"/api/v1/red-operativa/unidades/{created['idunidademergencia']}/invitacion/reenviar",
            {},
            format="json",
            **proveedor_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["idunidademergencia"] == created["idunidademergencia"]
        assert "invitacion_enviada" in data
        assert "password" not in data
        assert "temp_password" not in str(response.json())

    def test_reenviar_when_not_found_returns_404(self, api_client, proveedor_auth_headers):
        response = api_client.post(
            "/api/v1/red-operativa/unidades/999999/invitacion/reenviar",
            {},
            format="json",
            **proveedor_auth_headers,
        )
        assert response.status_code == 404

    def test_reenviar_when_admin_returns_403(self, api_client, admin_auth_headers):
        response = api_client.post(
            "/api/v1/red-operativa/unidades/1/invitacion/reenviar",
            {},
            format="json",
            **admin_auth_headers,
        )
        assert response.status_code == 403

    @patch(
        "apps.cuentas_clientes.services.onboarding_notificacion_service."
        "OnboardingNotificacionService.notify_invitacion",
        return_value=False,
    )
    def test_reenviar_when_smtp_fails_reports_error(
        self, _mock_notify, api_client, proveedor_auth_headers
    ):
        created = self._create_unidad(
            api_client, proveedor_auth_headers, placa="REENV-SMTP"
        )
        response = api_client.post(
            f"/api/v1/red-operativa/unidades/{created['idunidademergencia']}/invitacion/reenviar",
            {},
            format="json",
            **proveedor_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["invitacion_enviada"] is False
        assert data.get("invitacion_error")
