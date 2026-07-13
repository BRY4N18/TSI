"""Logout service — voluntary session close (RF-AUT-008)."""

from __future__ import annotations

from apps.cuentas_clientes.services.audit_service import AuditService
from core.repositories.cuentas_clientes.session_repository import SessionRepository


class LogoutError(Exception):
    """Logout failed."""


class LogoutService:
    """Closes the active session for the authenticated user."""

    def __init__(
        self,
        session_repo: SessionRepository | None = None,
        audit: AuditService | None = None,
    ):
        self.session_repo = session_repo or SessionRepository()
        self.audit = audit or AuditService()

    def logout(
        self,
        *,
        session_id: int,
        user_id: int,
        ip_address: str | None = None,
    ) -> dict:
        session = self.session_repo.close_session(session_id)
        if not session:
            raise LogoutError("Sesion no encontrada")

        if session.get("idusuario") != user_id:
            raise LogoutError("Sesion no pertenece al usuario")

        self.audit.log_logout(user_id, session_id, ip_address)

        return {
            "sessionId": session_id,
            "status": "Cierre sesion",
            "closedAt": session["fechahoracierresesion"],
        }
