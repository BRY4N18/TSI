import pytest

from apps.accidentes.services.evidencia_foto_service import EvidenciaFotoService
from core.storage.blob_storage_service import BlobStorageService


@pytest.mark.service
class TestEvidenciaFotoService:
    def test_subir_when_caso_activo_returns_sincronizado(
        self, mock_pinot, mock_kafka, accidente_activo, tmp_path
    ):
        # Arrange
        service = EvidenciaFotoService(blob_service=BlobStorageService(base_path=tmp_path))
        content = b"\xff\xd8\xff test"

        # Act
        result = service.subir(
            idaccidente=accidente_activo,
            idusuario=7,
            archivo=content,
            content_type="image/jpeg",
        )

        # Assert
        assert result["sincronizado"] is True
        assert result["idaccidente"] == accidente_activo
        assert "urlevidenciafoto" in result

    def test_subir_when_caso_cerrado_raises(self, mock_pinot, mock_kafka, tmp_path):
        # Arrange
        from apps.accidentes.domain_constants import ESTADO_CERRADO
        from core.repositories.accidentes.accidente_repository import (
            AccidenteRepository,
        )
        from core.repositories.accidentes.estado_accidente_repository import (
            EstadoAccidenteRepository,
        )

        AccidenteRepository().create({"idaccidente": "ACC-CLOSED", "activo": True})
        EstadoAccidenteRepository().append_estado(
            idaccidente="ACC-CLOSED", estado=ESTADO_CERRADO, idusuario=2
        )
        service = EvidenciaFotoService(blob_service=BlobStorageService(base_path=tmp_path))

        # Act / Assert
        with pytest.raises(ValueError):
            service.subir(
                idaccidente="ACC-CLOSED",
                idusuario=7,
                archivo=b"\xff\xd8\xff",
                content_type="image/jpeg",
            )
