"""Uniform API response helpers and exception handler."""

from __future__ import annotations

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def success_response(data, *, status_code=status.HTTP_200_OK, meta=None) -> Response:
    """Return standard success envelope {data, meta}."""
    return Response(
        {"data": data, "meta": meta or {"pagination": None}},
        status=status_code,
    )


def error_response(error: str, detail: str, code: str, *, status_code: int) -> Response:
    """Return standard error envelope {error, detail, code}."""
    return Response(
        {"error": error, "detail": detail, "code": code},
        status=status_code,
    )


def custom_exception_handler(exc, context):
    """Map exceptions to standard error envelope."""
    response = drf_exception_handler(exc, context)
    if response is not None:
        status_code = response.status_code
        detail = str(exc)
        if hasattr(exc, "detail"):
            if isinstance(exc.detail, dict):
                detail = "; ".join(f"{k}: {v}" for k, v in exc.detail.items())
            elif isinstance(exc.detail, list):
                detail = "; ".join(str(d) for d in exc.detail)
            else:
                detail = str(exc.detail)

        error_map = {
            400: "bad_request",
            401: "unauthorized",
            403: "forbidden",
            404: "not_found",
            409: "conflict",
        }
        response.data = {
            "error": error_map.get(status_code, "error"),
            "detail": detail,
            "code": str(status_code),
        }
    return response
