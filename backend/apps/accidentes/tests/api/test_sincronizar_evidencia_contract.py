import json
import uuid

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.mark.api
class TestSincronizarEvidenciaContract:
    def test_sincronizar_when_partial_returns_200(
        self, api_client, tecnico_auth_headers, accidente_activo, tmp_path, settings
    ):
        # Arrange
        settings.BLOB_STORAGE_LOCAL_PATH = tmp_path
        local_id = str(uuid.uuid4())
        notas = json.dumps(
            [
                {
                    "local_id": local_id,
                    "nota": "Offline note",
                    "tipo": "Observación general",
                    "fechahora": 1_700_000_000_000,
                }
            ]
        )

        # Act
        response = api_client.post(
            f"/api/v1/accidentes/{accidente_activo}/evidencias/sincronizar",
            {"notas": notas, "fotos_metadata": "[]"},
            format="multipart",
            **tecnico_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["sincronizados"] >= 1
        assert "resultados" in data

    def test_sincronizar_with_foto_returns_sincronizado(
        self, api_client, unidad_auth_headers, accidente_activo, tmp_path, settings
    ):
        # Arrange
        settings.BLOB_STORAGE_LOCAL_PATH = tmp_path
        local_id = str(uuid.uuid4())
        fotos_meta = json.dumps([{"local_id": local_id, "fechahora": 1_700_000_000_000}])
        foto = SimpleUploadedFile("f.jpg", b"\xff\xd8\xff", content_type="image/jpeg")

        # Act
        response = api_client.post(
            f"/api/v1/accidentes/{accidente_activo}/evidencias/sincronizar",
            {"fotos_metadata": fotos_meta, "fotos": foto},
            format="multipart",
            **unidad_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["sincronizados"] == 1
