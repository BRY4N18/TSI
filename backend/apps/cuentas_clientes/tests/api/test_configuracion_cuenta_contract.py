import pytest


@pytest.mark.api
class TestConfiguracionCuentaContract:
    def test_configurar_when_admin_returns_410_gone(
        self, api_client, auth_headers, mock_pinot, mock_kafka
    ):
        # Act — CU-O12 retirado
        response = api_client.patch(
            "/api/v1/cuentas-clientes/1/configuracion",
            {"plan_suscripcion": "premium"},
            format="json",
            **auth_headers,
        )

        # Assert
        assert response.status_code == 410
