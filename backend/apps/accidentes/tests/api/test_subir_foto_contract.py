import pytest
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.mark.api
class TestSubirFotoContract:
    def test_subir_when_valid_returns_201(
        self, api_client, tecnico_auth_headers, accidente_activo, tmp_path, settings
    ):
        # Arrange
        settings.BLOB_STORAGE_LOCAL_PATH = tmp_path
        foto = SimpleUploadedFile("test.jpg", b"\xff\xd8\xff\xe0", content_type="image/jpeg")

        # Act
        response = api_client.post(
            f"/api/v1/accidentes/{accidente_activo}/evidencias/fotos",
            {"archivo": foto},
            format="multipart",
            **tecnico_auth_headers,
        )

        # Assert
        assert response.status_code == 201
        body = response.json()
        assert body["data"]["sincronizado"] is True
        assert "urlevidenciafoto" in body["data"]

    def test_subir_when_admin_returns_403(
        self, api_client, admin_auth_headers, accidente_activo
    ):
        # Arrange
        foto = SimpleUploadedFile("test.jpg", b"\xff\xd8\xff", content_type="image/jpeg")

        # Act
        response = api_client.post(
            f"/api/v1/accidentes/{accidente_activo}/evidencias/fotos",
            {"archivo": foto},
            format="multipart",
            **admin_auth_headers,
        )

        # Assert
        assert response.status_code == 403
