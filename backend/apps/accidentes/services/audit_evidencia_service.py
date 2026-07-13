"""Audit logging for evidencia and disponibilidad operations."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("tsi.evidencia.audit")


class AuditEvidenciaService:
    def log_captura_foto(
        self,
        *,
        user_id: int,
        idaccidente: str,
        idevidenciafoto: int,
        extra: dict[str, Any] | None = None,
    ) -> None:
        logger.info(
            "evidencia_audit",
            extra={
                "action": "captura_foto",
                "idusuario": user_id,
                "idaccidente": idaccidente,
                "idevidenciafoto": idevidenciafoto,
                "details": extra or {},
            },
        )

    def log_captura_nota(
        self,
        *,
        user_id: int,
        idaccidente: str,
        idnotaaccidentes: int,
        extra: dict[str, Any] | None = None,
    ) -> None:
        logger.info(
            "evidencia_audit",
            extra={
                "action": "captura_nota",
                "idusuario": user_id,
                "idaccidente": idaccidente,
                "idnotaaccidentes": idnotaaccidentes,
                "details": extra or {},
            },
        )

    def log_sync_evidencia(
        self,
        *,
        user_id: int,
        idaccidente: str,
        sincronizados: int,
        pendientes: int,
        extra: dict[str, Any] | None = None,
    ) -> None:
        logger.info(
            "evidencia_audit",
            extra={
                "action": "sync_evidencia",
                "idusuario": user_id,
                "idaccidente": idaccidente,
                "sincronizados": sincronizados,
                "pendientes": pendientes,
                "details": extra or {},
            },
        )

    def log_cambio_disponibilidad(
        self,
        *,
        user_id: int,
        idunidademergencia: int,
        estadoanterior: str,
        estadonuevo: str,
        extra: dict[str, Any] | None = None,
    ) -> None:
        logger.info(
            "evidencia_audit",
            extra={
                "action": "cambio_disponibilidad",
                "idusuario": user_id,
                "idunidademergencia": idunidademergencia,
                "estadoanterior": estadoanterior,
                "estadonuevo": estadonuevo,
                "details": extra or {},
            },
        )
