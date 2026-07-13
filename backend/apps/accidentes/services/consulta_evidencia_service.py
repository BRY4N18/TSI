"""RF-EVI-005 — galería de evidencias sincronizadas."""

from __future__ import annotations

from typing import Any

from core.pinot.client import PinotClient
from core.repositories.evidencia.evidencia_foto_repository import EvidenciaFotoRepository
from core.repositories.evidencia.nota_campo_repository import NotaCampoRepository
from core.storage.blob_storage_service import BlobStorageService


class ConsultaEvidenciaService:
    def __init__(
        self,
        foto_repo: EvidenciaFotoRepository | None = None,
        nota_repo: NotaCampoRepository | None = None,
        pinot: PinotClient | None = None,
        blob_storage: BlobStorageService | None = None,
    ):
        self.foto_repo = foto_repo or EvidenciaFotoRepository()
        self.nota_repo = nota_repo or NotaCampoRepository()
        self.pinot = pinot or PinotClient()
        self.blob_storage = blob_storage or BlobStorageService()

    def _autor(self, idusuario: int) -> dict[str, Any]:
        rows = self.pinot.query(
            "SELECT idusuario, nombres, apellidos FROM Dim_Usuarios WHERE idusuario = %(idusuario)s LIMIT 1",
            {"idusuario": idusuario},
        )
        if rows:
            nombre = f"{rows[0].get('nombres', '')} {rows[0].get('apellidos', '')}".strip()
            return {"idusuario": idusuario, "nombre": nombre or f"Usuario {idusuario}"}
        return {"idusuario": idusuario, "nombre": f"Usuario {idusuario}"}

    def listar(
        self,
        idaccidente: str,
        *,
        tipo: str | None = None,
        limit: int = 20,
        cursor: str | None = None,
    ) -> tuple[list[dict[str, Any]], str | None]:
        cursor_int = int(cursor) if cursor else None

        fotos = self.foto_repo.list_by_accidente(
            idaccidente, limit=limit, cursor=cursor_int
        )
        notas = self.nota_repo.list_by_accidente(
            idaccidente, tipo=tipo, limit=limit, cursor=cursor_int
        )

        items: list[dict[str, Any]] = []
        for foto in fotos:
            items.append(
                {
                    "tipo": "foto",
                    "idevidenciafoto": foto["idevidenciafoto"],
                    "idaccidente": foto["idaccidente"],
                    "urlevidenciafoto": self.blob_storage.sign_read_url(foto["urlevidenciafoto"]),
                    "sincronizado": True,
                    "fechahora": foto["fechahora"],
                    "autor": self._autor(foto["idusuario"]),
                }
            )
        for nota in notas:
            items.append(
                {
                    "tipo_evidencia": "nota",
                    "idnotaaccidentes": nota["idnotaaccidentes"],
                    "idaccidente": nota["idaccidente"],
                    "nota": nota["nota"],
                    "tipo": nota["tipo"],
                    "sincronizado": True,
                    "fechahora": nota["fechahora"],
                    "autor": self._autor(nota["idusuario"]),
                }
            )

        items.sort(key=lambda x: x["fechahora"], reverse=True)
        items = items[:limit]

        next_cursor = None
        if len(items) == limit:
            last = items[-1]
            next_cursor = str(
                last.get("idevidenciafoto") or last.get("idnotaaccidentes")
            )

        return items, next_cursor
