"""Revoke session service — administrative session expulsion (CU-O07)."""

from __future__ import annotations

from apps.cuentas_clientes.services.audit_service import AuditService
from core.repositories.cuentas_clientes.session_repository import SessionRepository


class RevokeSessionError(Exception):
    """Revocation failed."""


class ForbiddenRevokeError(RevokeSessionError):
    """Caller lacks Administrator role."""


class RevokeSessionService:
    """Revokes an active session (admin only)."""

    ADMIN_ROLE = "Administrador"

    def __init__(
        self,
        session_repo: SessionRepository | None = None,
        audit: AuditService | None = None,
    ):
        self.session_repo = session_repo or SessionRepository()
        self.audit = audit or AuditService()

    def revoke(
        self,
        *,
        session_id: int,
        admin_id: int,
        admin_roles: list[str],
        ip_address: str | None = None,
    ) -> dict:
        if self.ADMIN_ROLE not in admin_roles:
            raise ForbiddenRevokeError("Privilegios insuficientes")

        session = self.session_repo.revoke_session(session_id)
        if not session:
            raise RevokeSessionError("Sesion no encontrada")

        self.audit.log_revoke(admin_id, session_id, ip_address)

        return {
            "sessionId": session_id,
            "status": "Expulsado",
            "revokedAt": session["fechahoracierresesion"],
        }
