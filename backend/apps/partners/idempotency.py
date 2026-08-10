"""Idempotency-Key para los endpoints de escritura de partners (api-standards).

Mismo contrato que `apps/suscripciones/idempotency.py` y `apps/red_operativa`:
si la peticion trae `Idempotency-Key`, la respuesta se cachea por actor y
ambito, y un reintento con la misma clave devuelve la respuesta original en
vez de ejecutar el efecto otra vez.

Por que aqui importa mas que en otros modulos
---------------------------------------------
`POST /partners/{id}/credenciales` devuelve el secreto en claro **una sola
vez** (RN-PON-005). Si el cliente pierde la respuesta por un timeout de red y
reintenta sin idempotencia, ocurre lo peor de ambos mundos: se emite una
credencial de mas y el secreto de la primera se pierde para siempre, porque
solo se persistio su hash. La idempotencia es lo que hace que un reintento
recupere el secreto original en lugar de generar basura irrecuperable.

Trade-off aceptado (Security vs Reliability)
--------------------------------------------
Cachear esa respuesta implica tener el secreto en claro en la cache durante
la ventana de reintento. Se acepta, pero se acota: el ambito de emision usa
`TTL_EMISION_SECONDS` (60 s, suficiente para un reintento automatico) en vez
de los 300 s del resto. No se elimina el secreto del cuerpo cacheado porque
eso vaciaria de sentido al reintento, que es justo el caso que protege.
"""

from __future__ import annotations

from django.core.cache import cache
from rest_framework.request import Request
from rest_framework.response import Response

TTL_SECONDS = 300

# Ventana corta a proposito: el cuerpo cacheado contiene el secreto en claro.
TTL_EMISION_SECONDS = 60

SCOPE_REGISTRO = "registro"
SCOPE_PLAN = "plan-acceso"
SCOPE_EMISION = "emision-credencial"
SCOPE_SOLICITUD = "solicitud-produccion"
SCOPE_RESOLUCION = "resolucion-produccion"

# Ambitos cuya respuesta lleva material sensible.
_SCOPES_SENSIBLES = {SCOPE_EMISION}


def _idusuario(request: Request) -> int | str:
    return getattr(getattr(request, "user", None), "idusuario", "anon")


def _cache_key(scope: str, request: Request, idempotency_key: str) -> str:
    return f"idempotency:partners:{scope}:{_idusuario(request)}:{idempotency_key}"


def _ttl(scope: str) -> int:
    return TTL_EMISION_SECONDS if scope in _SCOPES_SENSIBLES else TTL_SECONDS


def get_cached_response(request: Request, scope: str) -> Response | None:
    idempotency_key = request.headers.get("Idempotency-Key")
    if not idempotency_key:
        return None
    cached = cache.get(_cache_key(scope, request, idempotency_key))
    if cached is None:
        return None
    return Response(cached["data"], status=cached["status_code"])


def store_response(request: Request, scope: str, response: Response) -> None:
    """Solo se cachean respuestas exitosas.

    Un 409 no se cachea a proposito: si el conflicto se resuelve (por ejemplo,
    se le asigna el plan que faltaba), el mismo reintento debe poder triunfar.
    """
    idempotency_key = request.headers.get("Idempotency-Key")
    if not idempotency_key or response.status_code >= 400:
        return
    cache.set(
        _cache_key(scope, request, idempotency_key),
        {"data": response.data, "status_code": response.status_code},
        timeout=_ttl(scope),
    )
