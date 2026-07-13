"""JWT utilities for RS256 access tokens and opaque refresh tokens."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from django.conf import settings


class JWTError(Exception):
    """Base JWT validation error."""


class TokenExpiredError(JWTError):
    """Token has expired."""


class TokenInvalidError(JWTError):
    """Token is invalid."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(
    *,
    user_id: int,
    roles: list[str],
    session_id: int,
) -> str:
    """Create a signed RS256 access token with session_id claim."""
    now = _utcnow()
    payload = {
        "sub": str(user_id),
        "roles": roles,
        "session_id": session_id,
        "iat": int(now.timestamp()),
        "exp": int((now + settings.JWT_ACCESS_TOKEN_LIFETIME).timestamp()),
        "iss": settings.JWT_ISSUER,
    }
    return jwt.encode(
        payload,
        settings.JWT_PRIVATE_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def verify_access_token(token: str) -> dict[str, Any]:
    """Verify and decode an RS256 access token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_PUBLIC_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenExpiredError("Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenInvalidError("Invalid token") from exc

    if "session_id" not in payload:
        raise TokenInvalidError("Missing session_id claim")

    return payload


def create_refresh_token() -> str:
    """Create a static opaque refresh token (14-day lifetime enforced by caller)."""
    return secrets.token_urlsafe(48)


def create_session_token() -> str:
    """Create an opaque session identifier stored in Fact_Session."""
    return str(uuid.uuid4())


def refresh_token_expires_at() -> datetime:
    """Return expiry datetime for a new refresh token."""
    return _utcnow() + settings.JWT_REFRESH_TOKEN_LIFETIME
