import pytest


@pytest.mark.api
class TestOnboardingProgresoContract:
    def test_get_progreso_when_admin_local_returns_envelope(
        self, api_client, onboarding_cliente_auth_headers, mock_cuenta_pendiente_onboarding
    ):
        # Arrange
        cliente_id = mock_cuenta_pendiente_onboarding

        # Act
        response = api_client.get(
            f"/api/v1/cuentas-clientes/{cliente_id}/onboarding/progreso",
            **onboarding_cliente_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["estado_onboarding"] == "Pendiente"
        assert "etapas_completadas" in body["data"]
        assert body["data"]["etapa_actual"] == "cambio_password"
