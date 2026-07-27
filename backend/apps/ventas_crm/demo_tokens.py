"""Demo grant HMAC + demo session JWT helpers (not user RBAC JWT)."""
from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from datetime import datetime, timezone
from typing import Any

import jwt
from django.conf import settings


def _grant_secret() -> bytes:
    return str(getattr(settings, "DEMO_GRANT_SECRET", "dev-demo-grant-secret")).encode()


def _session_secret() -> str:
    return str(getattr(settings, "DEMO_SESSION_SECRET", "dev-demo-session-secret"))


def issue_demo_grant(idprospecto: int) -> str:
    nonce = secrets.token_hex(8)
    msg = f"{idprospecto}:{nonce}".encode()
    sig = hmac.new(_grant_secret(), msg, hashlib.sha256).hexdigest()
    return f"{idprospecto}.{nonce}.{sig}"


def verify_demo_grant(demo_grant: str, idprospecto: int) -> bool:
    try:
        raw_id, nonce, sig = demo_grant.split(".", 2)
        if int(raw_id) != int(idprospecto):
            return False
        expected = hmac.new(
            _grant_secret(), f"{idprospecto}:{nonce}".encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, sig)
    except (ValueError, TypeError, AttributeError):
        return False


def parse_iso_expiracion(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def format_iso_expiracion(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def issue_demo_session_token(*, idprospecto: int, demo_expiracion_iso: str) -> str:
    exp_dt = parse_iso_expiracion(demo_expiracion_iso)
    if exp_dt is None:
        raise ValueError("demo_expiracion inválida")
    payload = {
        "typ": "demo_session",
        "idprospecto": int(idprospecto),
        "exp": int(exp_dt.timestamp()),
        "iat": int(time.time()),
        "jti": secrets.token_hex(8),
    }
    return jwt.encode(payload, _session_secret(), algorithm="HS256")


def decode_demo_session_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, _session_secret(), algorithms=["HS256"])
