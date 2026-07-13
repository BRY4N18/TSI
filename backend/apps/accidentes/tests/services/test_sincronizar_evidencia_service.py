import json
import uuid

import pytest

from apps.accidentes.services.sincronizar_evidencia_service import SincronizarEvidenciaService
from core.storage.blob_storage_service import BlobStorageService, BlobUploadError


@pytest.mark.service
class TestSincronizarEvidenciaService:
    def test_sincronizar_when_partial_failure_returns_counts(
        self, mock_pinot, mock_kafka, accidente_activo, tmp_path, monkeypatch
    ):
        # Arrange
        from apps.accidentes.services.evidencia_foto_service import EvidenciaFotoService

        blob = BlobStorageService(base_path=tmp_path)
        service = SincronizarEvidenciaService(
            foto_service=EvidenciaFotoService(blob_service=blob)
        )
        local_ok = str(uuid.uuid4())
        local_fail = str(uuid.uuid4())
        notas = json.dumps(
            [
                {
                    "local_id": local_ok,
                    "nota": "Sync ok",
                    "tipo": "Observación general",
                    "fechahora": 1_700_000_000_000,
                }
            ]
        )
        fotos_meta = json.dumps(
            [
                {"local_id": local_fail, "fechahora": 1_700_000_000_001},
            ]
        )

        def fail_upload(**kwargs):
            raise BlobUploadError("Blob timeout")

        monkeypatch.setattr(blob, "upload", fail_upload)

        # Act
        result = service.sincronizar(
            idaccidente=accidente_activo,
            idusuario=7,
            notas_json=notas,
            fotos_metadata_json=fotos_meta,
            fotos_archivos=[(b"\xff\xd8\xff", "image/jpeg")],
        )

        # Assert
        assert result["sincronizados"] == 1
        assert result["pendientes"] == 1
