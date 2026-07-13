"""DRF views for despacho monitoring and SSE (RF-DES-011)."""

from __future__ import annotations

from django.http import StreamingHttpResponse
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accidentes.views.response_envelope import error_response, success_response
from apps.cuentas_clientes.permissions import IsAuthenticated401
from apps.despacho.permissions import IsOperadorDespacho
from apps.despacho.services.monitoreo_despacho_service import MonitoreoDespachoService


class MonitoreoDespachoView(APIView):
    permission_classes = [IsAuthenticated401, IsOperadorDespacho]

    def get(self, request: Request, idaccidente: str) -> Response:
        try:
            data = MonitoreoDespachoService().obtener_estado(idaccidente)
        except LookupError:
            return error_response("not_found", "Accidente no encontrado", "404", status_code=404)
        return success_response(data)


class MonitoreoDespachoStreamView(APIView):
    permission_classes = [IsAuthenticated401, IsOperadorDespacho]

    def get(self, request: Request, idaccidente: str) -> Response:
        svc = MonitoreoDespachoService()
        try:
            stream = svc.stream_eventos(idaccidente, timeout_sec=60.0)
            first = next(stream)
        except LookupError:
            return error_response("not_found", "Accidente no encontrado", "404", status_code=404)
        except StopIteration:
            return error_response("not_found", "Accidente no encontrado", "404", status_code=404)

        def event_stream():
            yield first
            yield from stream

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response
