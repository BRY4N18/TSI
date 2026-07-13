import base64

import pytest

from core.storage.blob_storage_service import (
    ALLOWED_CONTENT_TYPES,
    BlobStorageService,
    BlobTooLargeError,
)

FAKE_ACCOUNT_KEY = base64.b64encode(b"test-account-key-not-real-1234").decode()


@pytest.mark.service
class TestBlobStorageService:
    def test_upload_when_valid_returns_url(self, tmp_path):
        # Arrange
        service = BlobStorageService(base_path=tmp_path)
        content = b"\xff\xd8\xff fake jpeg"

        # Act
        url = service.upload(
            idaccidente="ACC-1",
            file_key="local-1",
            content=content,
            content_type="image/jpeg",
        )

        # Assert
        assert "ACC-1/local-1.jpg" in url
        assert (tmp_path / "evidencia-fotos" / "ACC-1" / "local-1.jpg").exists()

    def test_validate_file_when_too_large_raises(self):
        # Arrange
        service = BlobStorageService()
        huge = b"x" * (10 * 1024 * 1024 + 1)

        # Act / Assert
        with pytest.raises(BlobTooLargeError):
            service.validate_file(huge, "image/jpeg")

    def test_validate_file_when_invalid_type_raises(self):
        # Arrange
        service = BlobStorageService()

        # Act / Assert
        with pytest.raises(ValueError):
            service.validate_file(b"data", "application/pdf")

    def test_allowed_content_types_include_jpeg_and_png(self):
        # Assert
        assert "image/jpeg" in ALLOWED_CONTENT_TYPES
        assert "image/png" in ALLOWED_CONTENT_TYPES

    def test_sign_read_url_when_local_backend_returns_unchanged(self, tmp_path):
        # Arrange
        service = BlobStorageService(base_path=tmp_path)
        url = "https://accidentes.blob.core.windows.net/evidencia-fotos/ACC-1/x.jpg"

        # Act
        result = service.sign_read_url(url)

        # Assert
        assert result == url

    def test_sign_read_url_when_azure_configured_appends_sas_token(self, settings):
        # Arrange
        settings.BLOB_STORAGE_BACKEND = "azure"
        settings.AZURE_ACCOUNT_NAME = "accidentes"
        settings.AZURE_ACCOUNT_KEY = FAKE_ACCOUNT_KEY
        service = BlobStorageService()
        url = "https://accidentes.blob.core.windows.net/evidencia-fotos/ACC-1/x.jpg"

        # Act
        result = service.sign_read_url(url)

        # Assert
        assert result.startswith(f"{url}?")
        assert "sig=" in result

    def test_sign_read_url_when_host_mismatch_returns_unchanged(self, settings):
        # Arrange
        settings.BLOB_STORAGE_BACKEND = "azure"
        settings.AZURE_ACCOUNT_NAME = "accidentes"
        settings.AZURE_ACCOUNT_KEY = FAKE_ACCOUNT_KEY
        service = BlobStorageService()
        url = "https://other-host.example.com/evidencia-fotos/ACC-1/x.jpg"

        # Act
        result = service.sign_read_url(url)

        # Assert
        assert result == url

    def test_sign_read_url_when_no_account_key_returns_unchanged(self, settings):
        # Arrange
        settings.BLOB_STORAGE_BACKEND = "azure"
        settings.AZURE_ACCOUNT_NAME = "accidentes"
        settings.AZURE_ACCOUNT_KEY = ""
        service = BlobStorageService()
        url = "https://accidentes.blob.core.windows.net/evidencia-fotos/ACC-1/x.jpg"

        # Act
        result = service.sign_read_url(url)

        # Assert
        assert result == url
