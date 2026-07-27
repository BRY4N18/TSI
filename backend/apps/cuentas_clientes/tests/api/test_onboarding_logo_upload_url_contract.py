import pytest


@pytest.mark.api
class TestOnboardingLogoUploadUrlContract:
    def test_logo_upload_url_when_admin_returns_403(
        self, api_client, auth_headers, mock_cuenta_pendiente_onboarding
    ):
        # Arrange — Admin global ya no define branding (decisión 2026-07-24)
        cliente_id = mock_cuenta_pendiente_onboarding
        payload = {"content_type": "image/png", "file_name": "logo.png"}

        # Act
        response = api_client.post(
            f"/api/v1/cuentas-clientes/{cliente_id}/logo/upload-url",
            payload,
            format="json",
            **auth_headers,
        )

        # Assert
        assert response.status_code == 403

    def test_logo_upload_url_when_admin_local_returns_200(
        self, api_client, onboarding_cliente_auth_headers, mock_cuenta_pendiente_onboarding
    ):
        # Arrange
        cliente_id = mock_cuenta_pendiente_onboarding
        payload = {"content_type": "image/png", "file_name": "logo.png"}

        # Act
        response = api_client.post(
            f"/api/v1/cuentas-clientes/{cliente_id}/logo/upload-url",
            payload,
            format="json",
            **onboarding_cliente_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert "upload_url" in body["data"]
        assert "logo_url" in body["data"]
        assert "expires_at" in body["data"]
