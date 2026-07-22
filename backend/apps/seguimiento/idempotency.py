"""Idempotency-Key support for mi-seguimiento write endpoints (CU-O25/O26/O39).

Scope: only the 3 mi-seguimiento endpoints (see H1 in analysis). Uses Django's
default local-memory cache — no new infra — so a retried request (mobile GPS
ping resent after a timeout, a double tap on "Registrar llegada"/"Abortar
misión") replays the cached response instead of reprocessing.
"""

from __future__ import annotations

from django.core.cache import cache
from rest_framework.request import Request
from rest_framework.response import Response

TTL_SECONDS = 300


def _cache_key(scope: str, idusuario: int, idempotency_key: str) -> str:
    return f"idempotency:{scope}:{idusuario}:{idempotency_key}"


def get_cached_response(request: Request, scope: str) -> Response | None:
    """Return the cached Response for this Idempotency-Key, if any."""
    idempotency_key = request.headers.get("Idempotency-Key")
    if not idempotency_key:
        return None
    cached = cache.get(_cache_key(scope, request.user.idusuario, idempotency_key))
    if cached is None:
        return None
    return Response(cached["data"], status=cached["status_code"])


def store_response(request: Request, scope: str, response: Response) -> None:
    """Cache a successful response so a retry with the same key replays it."""
    idempotency_key = request.headers.get("Idempotency-Key")
    if not idempotency_key or response.status_code >= 400:
        return
    cache.set(
        _cache_key(scope, request.user.idusuario, idempotency_key),
        {"data": response.data, "status_code": response.status_code},
        timeout=TTL_SECONDS,
    )
