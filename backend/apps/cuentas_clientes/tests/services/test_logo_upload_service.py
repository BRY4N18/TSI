import pytest

from apps.cuentas_clientes.services.logo_upload_service import LogoUploadService


@pytest.mark.service
class TestLogoUploadService:
    def test_create_upload_url_when_valid_returns_urls(self, mock_pinot, mock_kafka):
        # Arrange
        service = LogoUploadService()

        # Act
        result = service.create_upload_url(
            user_id=3,
            roles=["Cliente"],
            cliente_id=1,
            content_type="image/png",
        )

        # Assert
        assert "upload_url" in result
        assert "logo_url" in result
        assert result["logo_url"].startswith("https://")
