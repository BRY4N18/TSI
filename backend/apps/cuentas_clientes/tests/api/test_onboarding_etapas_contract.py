import pytest


@pytest.mark.api
class TestOnboardingEtapasContract:
    def test_completar_etapa_when_valid_returns_progreso(
        self, api_client, onboarding_cliente_auth_headers, mock_cuenta_pendiente_onboarding
    ):
        # Arrange
        cliente_id = mock_cuenta_pendiente_onboarding
        payload = {"etapa": "cambio_password"}

        # Act
        response = api_client.post(
            f"/api/v1/cuentas-clientes/{cliente_id}/onboarding/etapas",
            payload,
            format="json",
            **onboarding_cliente_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["etapa"] == "cambio_password"
        assert "cambio_password" in body["data"]["progreso"]["etapas_completadas"]
