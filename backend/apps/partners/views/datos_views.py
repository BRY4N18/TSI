"""API de datos que consume el partner (CU-O51).

Esta es la unica superficie del proyecto que se autentica con credencial de
maquina en vez de con JWT humano. Todo lo demas de `partners/` son pantallas.

Un resultado vacio siempre es explicable
----------------------------------------
La respuesta incluye `meta.zonas_aplicadas` y `meta.severidades_aplicadas`. Sin
eso, un partner que recibe `[]` no puede distinguir «no hubo accidentes» de «no
tienes zonas contratadas», y acabaria abriendo un ticket para averiguarlo.
"""

from __future__ import annotations

from rest_framework import status
from rest_framework.views import APIView

from apps.partners.authentication import (
    CredencialAPIAuthentication,
    PartnerHabilitado,
)
from apps.partners.services.consumo_datos_service import (
    ConsumoDatosError,
    ConsumoDatosService,
)
from apps.partners.throttling import PartnerRateThrottle
from core.api.response_envelope import error_response, success_response

_HTTP_POR_CODIGO = {
    "validation_error": status.HTTP_400_BAD_REQUEST,
    "severidad_no_habilitada": status.HTTP_403_FORBIDDEN,
    "sin_suscripcion": status.HTTP_403_FORBIDDEN,
    "plan_incompleto": status.HTTP_422_UNPROCESSABLE_ENTITY,
}
_ERROR_POR_HTTP = {
    400: "bad_request",
    403: "forbidden",
    422: "unprocessable_entity",
}


class ConsultarAccidentesView(APIView):
    """GET /api/v1/datos/accidentes — expedientes dentro del alcance contratado."""

    authentication_classes = [CredencialAPIAuthentication]
    permission_classes = [PartnerHabilitado]
    throttle_classes = [PartnerRateThrottle]

    def get(self, request):
        usuario = request.user

        idseveridad = request.query_params.get("idseveridad")
        try:
            severidad = int(idseveridad) if idseveridad else None
            limit = int(request.query_params.get("limit", 50))
            desde = request.query_params.get("desde")
            hasta = request.query_params.get("hasta")
            desde_ms = int(desde) if desde else None
            hasta_ms = int(hasta) if hasta else None
        except (TypeError, ValueError):
            return error_response(
                "bad_request",
                "Los parámetros idseveridad, limit, desde y hasta deben ser enteros",
                "validation_error",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        try:
            resultado = ConsumoDatosService().consultar_accidentes(
                idcliente=usuario.idcliente,
                idseveridad=severidad,
                limit=limit,
                desde_ms=desde_ms,
                hasta_ms=hasta_ms,
            )
        except ConsumoDatosError as exc:
            http = _HTTP_POR_CODIGO.get(exc.code, status.HTTP_400_BAD_REQUEST)
            return error_response(
                _ERROR_POR_HTTP.get(http, "bad_request"),
                exc.detail,
                exc.code,
                status_code=http,
            )

        return success_response(resultado["items"], meta=resultado["meta"])
