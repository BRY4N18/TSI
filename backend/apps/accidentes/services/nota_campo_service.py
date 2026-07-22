"""RF-EVI-003 — registro de notas de campo."""

from __future__ import annotations

import time
from typing import Any

from core.audit.evidencia_service import AuditEvidenciaService
from core.repositories.evidencia.accidente_read_repository import (
    AccidenteReadRepository,
)
from core.repositories.evidencia.nota_campo_repository import NotaCampoRepository


class NotaCampoService:
    def __init__(
        self,
        accidente_repo: AccidenteReadRepository | None = None,
        nota_repo: NotaCampoRepository | None = None,
        audit: AuditEvidenciaService | None = None,
    ):
        self.accidente_repo = accidente_repo or AccidenteReadRepository()
        self.nota_repo = nota_repo or NotaCampoRepository()
        self.audit = audit or AuditEvidenciaService()

    def registrar(
        self,
        *,
        idaccidente: str,
        idusuario: int,
        nota: str,
        tipo: str,
        fechahora: int | None = None,
    ) -> dict[str, Any]:
        if not self.accidente_repo.find_by_id(idaccidente):
            raise LookupError("Accidente no encontrado")
        if not self.accidente_repo.is_caso_activo(idaccidente):
            raise ValueError("El caso no está activo para registrar evidencia")

        capture_ts = fechahora or int(time.time() * 1000)
        record = self.nota_repo.create_campo(
            idaccidente=idaccidente,
            idusuario=idusuario,
            nota=nota,
            tipo=tipo,
            fechahora=capture_ts,
        )
        self.audit.log_captura_nota(
            user_id=idusuario,
            idaccidente=idaccidente,
            idnotaaccidentes=record["idnotaaccidentes"],
        )
        return {
            "idnotaaccidentes": record["idnotaaccidentes"],
            "idaccidente": idaccidente,
            "nota": nota,
            "tipo": tipo,
            "sincronizado": True,
            "fechahora": capture_ts,
        }
