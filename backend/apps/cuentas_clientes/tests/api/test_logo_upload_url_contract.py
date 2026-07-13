import pytest


@pytest.mark.api
class TestLogoUploadUrlContract:
    def test_create_upload_url_when_valid_returns_envelope(self, api_client, cliente_auth_headers):
        # Arrange
        payload = {"content_type": "image/png"}

        # Act
        response = api_client.post(
            "/api/v1/cuentas-clientes/1/logo/upload-url",
            payload,
            format="json",
            **cliente_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()["data"]
        assert "upload_url" in data
        assert "logo_url" in data
