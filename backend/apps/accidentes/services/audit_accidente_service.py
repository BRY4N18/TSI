"""Audit logging for accident operations (RNF-REG-004)."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("tsi.accidentes.audit")


class AuditAccidenteService:
    """Records create/edit/discard/escalate/merge operations."""

    def log_action(
        self,
        *,
        action: str,
        user_id: int,
        idaccidente: str,
        fields_modified: list[str] | None = None,
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        logger.info(
            "accidente_audit",
            extra={
                "action": action,
                "idusuario": user_id,
                "idaccidente": idaccidente,
                "fields_modified": fields_modified or [],
                "old_values": old_values or {},
                "new_values": new_values or {},
                "details": extra or {},
            },
        )
