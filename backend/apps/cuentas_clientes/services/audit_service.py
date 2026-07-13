"""Security audit logging service."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("tsi.security.audit")


class AuditService:
    """Records security-relevant operations for traceability (RNF-AUT-003)."""

    def log_event(
        self,
        *,
        event_type: str,
        user_id: int | None,
        ip_address: str | None,
        result: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        logger.info(
            "security_event",
            extra={
                "event_type": event_type,
                "idusuario": user_id,
                "ip_address": ip_address,
                "result": result,
                "details": details or {},
            },
        )

    def log_login(self, user_id: int | None, ip_address: str | None, success: bool) -> None:
        self.log_event(
            event_type="login",
            user_id=user_id,
            ip_address=ip_address,
            result="success" if success else "failure",
        )

    def log_logout(self, user_id: int, session_id: int, ip_address: str | None) -> None:
        self.log_event(
            event_type="logout",
            user_id=user_id,
            ip_address=ip_address,
            result="success",
            details={"session_id": session_id},
        )

    def log_revoke(self, admin_id: int, session_id: int, ip_address: str | None) -> None:
        self.log_event(
            event_type="revoke_session",
            user_id=admin_id,
            ip_address=ip_address,
            result="success",
            details={"session_id": session_id},
        )

    def log_password_reset(self, user_id: int | None, ip_address: str | None, success: bool) -> None:
        self.log_event(
            event_type="password_reset",
            user_id=user_id,
            ip_address=ip_address,
            result="success" if success else "failure",
        )

    def log_cuenta_field_change(
        self,
        *,
        user_id: int,
        cliente_id: int,
        field: str,
        old_value,
        new_value,
        ip_address: str | None = None,
    ) -> None:
        self.log_event(
            event_type="cuenta_field_change",
            user_id=user_id,
            ip_address=ip_address,
            result="success",
            details={
                "idcliente": cliente_id,
                "field": field,
                "old_value": old_value,
                "new_value": new_value,
            },
        )

    def log_transferencia(
        self,
        *,
        user_id: int,
        cliente_id: int,
        anterior_admin_id: int,
        nuevo_admin_id: int,
        ip_address: str | None = None,
    ) -> None:
        self.log_event(
            event_type="transferencia_propiedad",
            user_id=user_id,
            ip_address=ip_address,
            result="success",
            details={
                "idcliente": cliente_id,
                "admin_local_anterior_id": anterior_admin_id,
                "nuevo_admin_local_id": nuevo_admin_id,
            },
        )

    def log_baja_cuenta(
        self,
        *,
        user_id: int,
        cliente_id: int,
        motivo: str | None,
        ip_address: str | None = None,
    ) -> None:
        details: dict = {"idcliente": cliente_id}
        if motivo:
            details["motivo"] = motivo
        self.log_event(
            event_type="baja_cuenta",
            user_id=user_id,
            ip_address=ip_address,
            result="success",
            details=details,
        )

    def log_smtp_failure(
        self,
        *,
        user_id: int,
        cliente_id: int,
        event: str,
        error: str,
    ) -> None:
        self.log_event(
            event_type="smtp_failure",
            user_id=user_id,
            ip_address=None,
            result="failure",
            details={"idcliente": cliente_id, "event": event, "error": error},
        )

    def log_registro_cuenta(
        self,
        *,
        user_id: int,
        cliente_id: int,
        nit: str,
        ip_address: str | None = None,
    ) -> None:
        self.log_event(
            event_type="registro_cuenta",
            user_id=user_id,
            ip_address=ip_address,
            result="success",
            details={"idcliente": cliente_id, "nit": nit},
        )

    def log_configuracion_cuenta(
        self,
        *,
        user_id: int,
        cliente_id: int,
        plan_suscripcion: str,
        ip_address: str | None = None,
    ) -> None:
        self.log_event(
            event_type="configuracion_cuenta",
            user_id=user_id,
            ip_address=ip_address,
            result="success",
            details={"idcliente": cliente_id, "plan_suscripcion": plan_suscripcion},
        )

    def log_onboarding_etapa(
        self,
        *,
        user_id: int,
        cliente_id: int,
        etapa: str,
        ip_address: str | None = None,
    ) -> None:
        self.log_event(
            event_type="onboarding_etapa",
            user_id=user_id,
            ip_address=ip_address,
            result="success",
            details={"idcliente": cliente_id, "etapa": etapa},
        )

    def log_reenvio_invitacion(
        self,
        *,
        user_id: int,
        target_user_id: int,
        cliente_id: int,
        ip_address: str | None = None,
    ) -> None:
        self.log_event(
            event_type="reenvio_invitacion",
            user_id=user_id,
            ip_address=ip_address,
            result="success",
            details={"idcliente": cliente_id, "id_usuario": target_user_id},
        )

    def log_onboarding_reminder(
        self,
        *,
        cliente_id: int,
        admin_local_id: int,
    ) -> None:
        self.log_event(
            event_type="onboarding_reminder",
            user_id=admin_local_id,
            ip_address=None,
            result="success",
            details={"idcliente": cliente_id, "evento": "reminder"},
        )
