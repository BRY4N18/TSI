"""Vistas de solicitud y resolucion de la promocion a produccion (CU-O49)."""

from __future__ import annotations

from rest_framework import status
from rest_framework.views import APIView

from apps.partners.idempotency import (
    SCOPE_RESOLUCION,
    SCOPE_SOLICITUD,
    get_cached_response,
    store_response,
)
from apps.partners.permissions import (
    EsAdministrador,
    EsPartner,
    PropiedadPartnerError,
    verificar_propiedad,
)
from apps.partners.services.audit_partner_service import AuditPartnerService
from apps.partners.services.promocion_produccion_service import (
    PromocionProduccionError,
    PromocionProduccionService,
)
from core.repositories.partners.partner_repository import PartnerRepository
from core.api.response_envelope import error_response, success_response

_HTTP_POR_CODIGO = {
    "validation_error": status.HTTP_400_BAD_REQUEST,
    "not_found": status.HTTP_404_NOT_FOUND,
    "ruta_invalida": status.HTTP_409_CONFLICT,
    "sin_solicitud_pendiente": status.HTTP_409_CONFLICT,
    "partner_suspendido": status.HTTP_409_CONFLICT,
    "sin_plan": status.HTTP_409_CONFLICT,
    "nombre_duplicado": status.HTTP_409_CONFLICT,
    "motivo_requerido": status.HTTP_422_UNPROCESSABLE_ENTITY,
}
_ERROR_POR_HTTP = {
    400: "bad_request",
    404: "not_found",
    409: "conflict",
    422: "unprocessable_entity",
}


def _fallo(exc):
    http = _HTTP_POR_CODIGO.get(exc.code, status.HTTP_400_BAD_REQUEST)
    return error_response(
        _ERROR_POR_HTTP.get(http, "bad_request"), exc.detail, exc.code, status_code=http
    )


class SolicitudProduccionView(APIView):
    """POST: el partner solicita el paso a produccion (RF-PON-007).

    Devuelve 202, no 201: la activacion efectiva requiere intervencion humana.
    """

    permission_classes = [EsPartner]

    def post(self, request, idpartner: int):
        if (cacheada := get_cached_response(request, SCOPE_SOLICITUD)) is not None:
            return cacheada
        try:
            verificar_propiedad(request, PartnerRepository().find_by_id(int(idpartner)))
        except PropiedadPartnerError as exc:
            AuditPartnerService().log_denegacion(
                idpartner=int(idpartner),
                idusuario=getattr(getattr(request, "user", None), "idusuario", None),
                motivo=str(exc),
            )
            return error_response(
                "forbidden", str(exc), "propiedad_partner", status_code=status.HTTP_403_FORBIDDEN
            )
        try:
            resultado = PromocionProduccionService().solicitar(
                idpartner=int(idpartner),
                nombre_credencial=str(request.data.get("nombre_credencial") or ""),
            )
        except PromocionProduccionError as exc:
            return _fallo(exc)
        respuesta = success_response(resultado, status_code=status.HTTP_202_ACCEPTED)
        store_response(request, SCOPE_SOLICITUD, respuesta)
        return respuesta


class ResolucionProduccionView(APIView):
    """POST: SOLO el Administrador aprueba o rechaza (RF-PON-008)."""

    permission_classes = [EsAdministrador]

    def post(self, request, idpartner: int):
        if (cacheada := get_cached_response(request, SCOPE_RESOLUCION)) is not None:
            return cacheada
        try:
            resultado = PromocionProduccionService().resolver(
                idpartner=int(idpartner),
                decision=str(request.data.get("decision") or ""),
                motivo=request.data.get("motivo"),
            )
        except PromocionProduccionError as exc:
            return _fallo(exc)
        AuditPartnerService().log_promocion(
            idpartner=int(idpartner),
            idusuario=getattr(getattr(request, "user", None), "idusuario", None),
            decision=str(request.data.get("decision") or ""),
            motivo=str(request.data.get("motivo") or ""),
        )
        respuesta = success_response(resultado)
        store_response(request, SCOPE_RESOLUCION, respuesta)
        return respuesta
