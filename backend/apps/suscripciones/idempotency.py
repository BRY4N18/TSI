"""Idempotency-Key for suscripciones write endpoints (api-standards)."""

from __future__ import annotations

from django.core.cache import cache
from rest_framework.request import Request
from rest_framework.response import Response

TTL_SECONDS = 300


def _cache_key(scope: str, idusuario: int, idempotency_key: str) -> str:
    return f"idempotency:suscripciones:{scope}:{idusuario}:{idempotency_key}"


def get_cached_response(request: Request, scope: str) -> Response | None:
    idempotency_key = request.headers.get("Idempotency-Key")
    if not idempotency_key:
        return None
    cached = cache.get(_cache_key(scope, request.user.idusuario, idempotency_key))
    if cached is None:
        return None
    return Response(cached["data"], status=cached["status_code"])


def store_response(request: Request, scope: str, response: Response) -> None:
    idempotency_key = request.headers.get("Idempotency-Key")
    if not idempotency_key or response.status_code >= 400:
        return
    cache.set(
        _cache_key(scope, request.user.idusuario, idempotency_key),
        {"data": response.data, "status_code": response.status_code},
        timeout=TTL_SECONDS,
    )


def require_idempotency_key(request: Request) -> str | None:
    return request.headers.get("Idempotency-Key")
