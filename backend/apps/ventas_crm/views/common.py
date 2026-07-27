from rest_framework import status
from core.api.response_envelope import error_response
from apps.ventas_crm.domain import (
    ValidationError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)

def crm_error(exc):
    mapping = (
        (ValidationError, "bad_request", 400),
        (ConflictError, "conflict", 409),
        (ForbiddenError, "forbidden", 403),
        (NotFoundError, "not_found", 404),
        (UnauthorizedError, "unauthorized", 401),
    )
    for exc_type, code, http in mapping:
        if isinstance(exc, exc_type):
            return error_response(code, str(exc), str(http), status_code=http)
    raise exc

def roles(request): return list(getattr(request.user, "roles", []) or [])
