"""Vistas mapa operador + SSE."""

from __future__ import annotations

from django.http import StreamingHttpResponse
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accidentes.views.response_envelope import error_response, success_response
from apps.cuentas_clientes.permissions import IsAuthenticated401
from apps.seguimiento.permissions import IsOperadorSeguimiento
from apps.seguimiento.services.mapa_seguimiento_service import MapaSeguimientoService
from apps.seguimiento.services.seguimiento_sse_service import SeguimientoSseService


class MapaSeguimientoView(APIView):
    permission_classes = [IsAuthenticated401, IsOperadorSeguimiento]

    def get(self, request: Request) -> Response:
        data = MapaSeguimientoService().obtener_mapa()
        return success_response(data)


class SeguimientoStreamView(APIView):
    permission_classes = [IsAuthenticated401, IsOperadorSeguimiento]

    def get(self, request: Request) -> StreamingHttpResponse:
        sse = SeguimientoSseService()
        response = StreamingHttpResponse(
            sse.stream_events(),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response


class SeguimientoAccidenteView(APIView):
    permission_classes = [IsAuthenticated401, IsOperadorSeguimiento]

    def get(self, request: Request, idaccidente: str) -> Response:
        data = MapaSeguimientoService().obtener_seguimiento_accidente(idaccidente)
        if not data:
            return error_response("not_found", "Accidente no encontrado", "404", status_code=404)
        return success_response(data)
