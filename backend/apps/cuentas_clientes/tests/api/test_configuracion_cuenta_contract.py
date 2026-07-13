import pytest


@pytest.mark.api
class TestConfiguracionCuentaContract:
    def test_configurar_when_admin_returns_200(self, api_client, auth_headers, mock_pinot, mock_kafka):
        # Arrange — register account first
        registro = {
            "razon_social": "Config Test S.A.",
            "nombre": "Config",
            "tipo": "Aseguradora",
            "nit_identificacion": "701234567-8",
            "fecha_inicio_contrato": 1704067200000,
            "admin_local": {
                "nombres": "Config",
                "apellidos": "Admin",
                "gmail": "config.admin@tsi.com",
            },
        }
        created = api_client.post(
            "/api/v1/cuentas-clientes", registro, format="json", **auth_headers
        )
        cliente_id = created.json()["data"]["idcliente"]
        payload = {"plan_suscripcion": "premium", "logo_url": "https://cdn.example.com/logo.png"}

        # Act
        response = api_client.patch(
            f"/api/v1/cuentas-clientes/{cliente_id}/configuracion",
            payload,
            format="json",
            **auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["estado_onboarding"] == "Pendiente"
        assert body["data"]["plan_suscripcion"] == "premium"
