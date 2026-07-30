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

    def log_enriquecer_clima(self, *, user_id: int, idaccidente: str) -> None:
        logger.info(
            "evidencia_audit",
            extra={
                "action": "enriquecer_clima",
                "idusuario": user_id,
                "idaccidente": idaccidente,
            },
        )

    def log_enriquecer_elemento_fisico(
        self, *, user_id: int, idaccidente: str, idelementofisico: int
    ) -> None:
        logger.info(
            "evidencia_audit",
            extra={
                "action": "enriquecer_elemento_fisico",
                "idusuario": user_id,
                "idaccidente": idaccidente,
                "idelementofisico": idelementofisico,
            },
        )

    def log_registrar_conductor_accidente(
        self, *, user_id: int, idaccidente: str, idconductoraccidente: int
    ) -> None:
        logger.info(
            "evidencia_audit",
            extra={
                "action": "registrar_conductor_accidente",
                "idusuario": user_id,
                "idaccidente": idaccidente,
                "idconductoraccidente": idconductoraccidente,
            },
        )

    def log_consultar_conductores_accidente(
        self, *, user_id: int, idaccidente: str, count: int
    ) -> None:
        logger.info(
            "evidencia_audit",
            extra={
                "action": "consultar_conductores_accidente",
                "idusuario": user_id,
                "idaccidente": idaccidente,
                "count": count,
            },
        )

    def log_desactivar_conductor_accidente(
        self, *, user_id: int, idaccidente: str, idconductoraccidente: int
    ) -> None:
        logger.info(
            "evidencia_audit",
            extra={
                "action": "desactivar_conductor_accidente",
                "idusuario": user_id,
                "idaccidente": idaccidente,
                "idconductoraccidente": idconductoraccidente,
            },
        )

    def log_registrar_implicado_accidente(
        self, *, user_id: int, idaccidente: str, idimplicado: int
    ) -> None:
        logger.info(
            "evidencia_audit",
            extra={
                "action": "registrar_implicado_accidente",
                "idusuario": user_id,
                "idaccidente": idaccidente,
                "idimplicado": idimplicado,
            },
        )

    def log_consultar_implicados_accidente(
        self, *, user_id: int, idaccidente: str, count: int
    ) -> None:
        logger.info(
            "evidencia_audit",
            extra={
                "action": "consultar_implicados_accidente",
                "idusuario": user_id,
                "idaccidente": idaccidente,
                "count": count,
            },
        )

    def log_desactivar_implicado_accidente(
        self, *, user_id: int, idaccidente: str, idimplicado: int
    ) -> None:
        logger.info(
            "evidencia_audit",
            extra={
                "action": "desactivar_implicado_accidente",
                "idusuario": user_id,
                "idaccidente": idaccidente,
                "idimplicado": idimplicado,
            },
        )
