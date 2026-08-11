"""Suspension y reactivacion manual del acceso (CU-O55, RF-PAC-005).

**Solo Administrador**, en las dos. Y la reactivacion no tiene equivalente
automatico en ningun job del sistema: reabrir un acceso cortado es siempre una
decision humana (RN-PAC-009).
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.views import APIView

from apps.partners.idempotency import (
    SCOPE_RESOLUCION,
    get_cached_response,
    store_response,
)
from apps.partners.permissions import EsAdministrador
from apps.partners.services.reactivar_partner_service import (
    ReactivarPartnerError,
    ReactivarPartnerService,
)
from apps.partners.services.suspender_partner_service import (
    SuspenderPartnerError,
    SuspenderPartnerService,
)
from core.api.response_envelope import error_response, success_response

_HTTP_POR_CODIGO = {
    "validation_error": status.HTTP_400_BAD_REQUEST,
    "not_found": status.HTTP_404_NOT_FOUND,
    "partner_ya_suspendido": status.HTTP_409_CONFLICT,
    "partner_no_suspendido": status.HTTP_409_CONFLICT,
}
_ERROR_POR_HTTP = {400: "bad_request", 404: "not_found", 409: "conflict"}


def _error(exc) -> object:
    http = _HTTP_POR_CODIGO.get(exc.code, status.HTTP_400_BAD_REQUEST)
    return error_response(
        _ERROR_POR_HTTP.get(http, "bad_request"), exc.detail, exc.code, status_code=http
    )


class SuspenderPartnerView(APIView):
    """POST /api/v1/partners/{idpartner}/suspender — motivo OBLIGATORIO."""

    permission_classes = [EsAdministrador]

    def post(self, request, idpartner: int):
        if (cacheada := get_cached_response(request, SCOPE_RESOLUCION)) is not None:
            return cacheada
        try:
            resultado = SuspenderPartnerService().suspender(
                idpartner=int(idpartner),
                motivo=str(request.data.get("motivo") or ""),
                automatica=False,
            )
        except SuspenderPartnerError as exc:
            return _error(exc)

        respuesta = success_response(resultado)
        store_response(request, SCOPE_RESOLUCION, respuesta)
        return respuesta


class ReactivarPartnerView(APIView):
    """POST /api/v1/partners/{idpartner}/reactivar — motivo opcional.

    La respuesta desglosa `credenciales_restituidas` y
    `credenciales_no_restituidas` a proposito: hace **visible** que no todas
    vuelven. Si el Administrador esperaba tres y ve dos, la respuesta ya le dijo
    que una estaba revocada por seguridad y no debe resucitar (RN-PAC-011).
    """

    permission_classes = [EsAdministrador]

    def post(self, request, idpartner: int):
        if (cacheada := get_cached_response(request, SCOPE_RESOLUCION)) is not None:
            return cacheada
        try:
            resultado = ReactivarPartnerService().reactivar(
                idpartner=int(idpartner),
                motivo=str(request.data.get("motivo") or ""),
            )
        except ReactivarPartnerError as exc:
            return _error(exc)

        respuesta = success_response(resultado)
        store_response(request, SCOPE_RESOLUCION, respuesta)
        return respuesta
