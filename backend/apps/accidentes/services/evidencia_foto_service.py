"""RF-EVI-002 — subida de evidencia fotográfica."""

from __future__ import annotations

import time
from typing import Any

from apps.accidentes.services.audit_evidencia_service import AuditEvidenciaService
from core.repositories.evidencia.accidente_read_repository import AccidenteReadRepository
from core.repositories.evidencia.evidencia_foto_repository import EvidenciaFotoRepository
from core.storage.blob_storage_service import (
    BlobStorageService,
    BlobTooLargeError,
    BlobUploadError,
)


class EvidenciaFotoService:
    def __init__(
        self,
        accidente_repo: AccidenteReadRepository | None = None,
        evidencia_repo: EvidenciaFotoRepository | None = None,
        blob_service: BlobStorageService | None = None,
        audit: AuditEvidenciaService | None = None,
    ):
        self.accidente_repo = accidente_repo or AccidenteReadRepository()
        self.evidencia_repo = evidencia_repo or EvidenciaFotoRepository()
        self.blob_service = blob_service or BlobStorageService()
        self.audit = audit or AuditEvidenciaService()

    def subir(
        self,
        *,
        idaccidente: str,
        idusuario: int,
        archivo: bytes,
        content_type: str,
        fechahora: int | None = None,
    ) -> dict[str, Any]:
        if not self.accidente_repo.find_by_id(idaccidente):
            raise LookupError("Accidente no encontrado")
        if not self.accidente_repo.is_caso_activo(idaccidente):
            raise ValueError("El caso no está activo para registrar evidencia")

        capture_ts = fechahora or int(time.time() * 1000)
        file_key = self.blob_service.generate_file_key()

        try:
            url = self.blob_service.upload(
                idaccidente=idaccidente,
                file_key=file_key,
                content=archivo,
                content_type=content_type,
            )
        except BlobTooLargeError:
            raise
        except BlobUploadError as exc:
            raise BlobUploadError(str(exc)) from exc

        record = self.evidencia_repo.create(
            idaccidente=idaccidente,
            idusuario=idusuario,
            urlevidenciafoto=url,
            fechahora=capture_ts,
        )
        self.audit.log_captura_foto(
            user_id=idusuario,
            idaccidente=idaccidente,
            idevidenciafoto=record["idevidenciafoto"],
        )
        return {
            "idevidenciafoto": record["idevidenciafoto"],
            "idaccidente": idaccidente,
            "urlevidenciafoto": url,
            "sincronizado": True,
            "fechahora": capture_ts,
        }
