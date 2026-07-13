"""Session validation service — JWT + Fact_Session per request."""

from __future__ import annotations

from core.jwt_utils import TokenExpiredError, TokenInvalidError, verify_access_token
from core.repositories.cuentas_clientes.session_repository import SessionRepository


class SessionValidationError(Exception):
    """Session is not valid for access."""


class SessionValidationService:
    """Validates JWT signature and session state on each protected request."""

    def __init__(self, session_repo: SessionRepository | None = None):
        self.session_repo = session_repo or SessionRepository()

    def validate_token_and_session(self, token: str) -> dict:
        try:
            claims = verify_access_token(token)
        except TokenExpiredError as exc:
            raise SessionValidationError("Token expired") from exc
        except TokenInvalidError as exc:
            raise SessionValidationError("Invalid token") from exc

        session_id = int(claims["session_id"])
        if not self.session_repo.is_active(session_id):
            raise SessionValidationError("Session closed or revoked")

        return claims
