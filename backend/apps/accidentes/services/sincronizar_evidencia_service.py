"""CU-O43 — sincronización diferida de evidencia offline."""

from __future__ import annotations

import json
from typing import Any

from apps.accidentes.services.audit_evidencia_service import AuditEvidenciaService
from apps.accidentes.services.evidencia_foto_service import EvidenciaFotoService
from apps.accidentes.services.nota_campo_service import NotaCampoService
from core.storage.blob_storage_service import BlobTooLargeError, BlobUploadError


class SincronizarEvidenciaService:
    def __init__(
        self,
        foto_service: EvidenciaFotoService | None = None,
        nota_service: NotaCampoService | None = None,
        audit: AuditEvidenciaService | None = None,
    ):
        self.foto_service = foto_service or EvidenciaFotoService()
        self.nota_service = nota_service or NotaCampoService()
        self.audit = audit or AuditEvidenciaService()

    def sincronizar(
        self,
        *,
        idaccidente: str,
        idusuario: int,
        notas_json: str | None,
        fotos_metadata_json: str | None,
        fotos_archivos: list[tuple[bytes, str]],
    ) -> dict[str, Any]:
        resultados: list[dict[str, Any]] = []
        sincronizados = 0
        pendientes = 0

        notas = json.loads(notas_json) if notas_json else []
        fotos_meta = json.loads(fotos_metadata_json) if fotos_metadata_json else []

        for nota_item in notas:
            local_id = nota_item["local_id"]
            try:
                record = self.nota_service.registrar(
                    idaccidente=idaccidente,
                    idusuario=idusuario,
                    nota=nota_item["nota"],
                    tipo=nota_item["tipo"],
                    fechahora=nota_item["fechahora"],
                )
                sincronizados += 1
                resultados.append(
                    {
                        "local_id": local_id,
                        "sincronizado": True,
                        "idevidenciafoto": None,
                        "idnotaaccidentes": record["idnotaaccidentes"],
                        "urlevidenciafoto": None,
                        "error": None,
                    }
                )
            except Exception as exc:
                pendientes += 1
                resultados.append(
                    {
                        "local_id": local_id,
                        "sincronizado": False,
                        "idevidenciafoto": None,
                        "idnotaaccidentes": None,
                        "urlevidenciafoto": None,
                        "error": str(exc),
                    }
                )

        for idx, meta in enumerate(fotos_meta):
            local_id = meta["local_id"]
            if idx >= len(fotos_archivos):
                pendientes += 1
                resultados.append(
                    {
                        "local_id": local_id,
                        "sincronizado": False,
                        "idevidenciafoto": None,
                        "idnotaaccidentes": None,
                        "urlevidenciafoto": None,
                        "error": "Archivo faltante",
                    }
                )
                continue

            content, content_type = fotos_archivos[idx]
            try:
                record = self.foto_service.subir(
                    idaccidente=idaccidente,
                    idusuario=idusuario,
                    archivo=content,
                    content_type=content_type,
                    fechahora=meta["fechahora"],
                )
                sincronizados += 1
                resultados.append(
                    {
                        "local_id": local_id,
                        "sincronizado": True,
                        "idevidenciafoto": record["idevidenciafoto"],
                        "idnotaaccidentes": None,
                        "urlevidenciafoto": record["urlevidenciafoto"],
                        "error": None,
                    }
                )
            except (BlobTooLargeError, BlobUploadError, LookupError, ValueError) as exc:
                pendientes += 1
                resultados.append(
                    {
                        "local_id": local_id,
                        "sincronizado": False,
                        "idevidenciafoto": None,
                        "idnotaaccidentes": None,
                        "urlevidenciafoto": None,
                        "error": str(exc),
                    }
                )

        self.audit.log_sync_evidencia(
            user_id=idusuario,
            idaccidente=idaccidente,
            sincronizados=sincronizados,
            pendientes=pendientes,
        )
        return {
            "sincronizados": sincronizados,
            "pendientes": pendientes,
            "resultados": resultados,
        }
