"""CU-O43 — sincronización diferida de evidencia offline."""

from __future__ import annotations

import json
from typing import Any

from apps.accidentes.services.evidencia_foto_service import EvidenciaFotoService
from apps.accidentes.services.nota_campo_service import NotaCampoService
from core.audit.evidencia_service import AuditEvidenciaService
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
        enriquecimiento_json: str | None = None,
    ) -> dict[str, Any]:
        from apps.accidentes.services.enriquecimiento_clima_service import (
            EnriquecimientoClimaService,
        )
        from apps.accidentes.services.enriquecimiento_conductor_service import (
            EnriquecimientoConductorService,
        )
        from apps.accidentes.services.enriquecimiento_elemento_fisico_service import (
            EnriquecimientoElementoFisicoService,
        )
        from apps.accidentes.services.enriquecimiento_implicado_service import (
            EnriquecimientoImplicadoService,
        )

        resultados: list[dict[str, Any]] = []
        sincronizados = 0
        pendientes = 0

        notas = json.loads(notas_json) if notas_json else []
        fotos_meta = json.loads(fotos_metadata_json) if fotos_metadata_json else []
        enriquecimiento = json.loads(enriquecimiento_json) if enriquecimiento_json else {}

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

        clima = enriquecimiento.get("clima")
        if clima:
            local_id = clima.get("local_id", "clima")
            try:
                EnriquecimientoClimaService().upsert(
                    idaccidente=idaccidente,
                    idusuario=idusuario,
                    idperiododia=clima.get("idperiododia"),
                    idestadoclima=clima.get("idestadoclima"),
                )
                sincronizados += 1
                resultados.append(
                    {"local_id": local_id, "sincronizado": True, "error": None}
                )
            except Exception as exc:
                pendientes += 1
                resultados.append(
                    {"local_id": local_id, "sincronizado": False, "error": str(exc)}
                )

        for item in enriquecimiento.get("elementos_fisicos") or []:
            local_id = item.get("local_id", f"fisico-{item.get('idelementofisico')}")
            try:
                EnriquecimientoElementoFisicoService().agregar(
                    idaccidente=idaccidente,
                    idelementofisico=int(item["idelementofisico"]),
                    idusuario=idusuario,
                )
                sincronizados += 1
                resultados.append(
                    {"local_id": local_id, "sincronizado": True, "error": None}
                )
            except Exception as exc:
                pendientes += 1
                resultados.append(
                    {"local_id": local_id, "sincronizado": False, "error": str(exc)}
                )

        for item in enriquecimiento.get("conductores") or []:
            local_id = item.get("local_id", "conductor")
            try:
                EnriquecimientoConductorService().registrar(
                    idaccidente=idaccidente,
                    idusuario=idusuario,
                    conductor=item["conductor"],
                    idestadoconductor=int(item["idestadoconductor"]),
                    vehiculo=item["vehiculo"],
                )
                sincronizados += 1
                resultados.append(
                    {"local_id": local_id, "sincronizado": True, "error": None}
                )
            except Exception as exc:
                pendientes += 1
                resultados.append(
                    {"local_id": local_id, "sincronizado": False, "error": str(exc)}
                )

        for item in enriquecimiento.get("implicados") or []:
            local_id = item.get("local_id", "implicado")
            try:
                EnriquecimientoImplicadoService().registrar(
                    idaccidente=idaccidente,
                    idusuario=idusuario,
                    tipoimplicado=item["tipoimplicado"],
                    estadoimplicado=item["estadoimplicado"],
                    genero=item.get("genero"),
                    edad=item.get("edad"),
                )
                sincronizados += 1
                resultados.append(
                    {"local_id": local_id, "sincronizado": True, "error": None}
                )
            except Exception as exc:
                pendientes += 1
                resultados.append(
                    {"local_id": local_id, "sincronizado": False, "error": str(exc)}
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
