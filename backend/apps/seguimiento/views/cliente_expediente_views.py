"""Vistas expedientes cliente (RF-SEG-006)."""

from __future__ import annotations

from django.http import HttpResponse
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.seguimiento.permissions import IsClienteExpediente
from apps.seguimiento.services.expediente_pdf_service import ExpedientePdfService
from apps.seguimiento.services.expediente_service import ExpedienteService
from apps.seguimiento.services.historial_emergencias_service import (
    HistorialEmergenciasService,
)
from core.api.response_envelope import error_response, success_response
from core.auth.permissions import IsAuthenticated401
from core.pinot.client import PinotClient


class ClienteExpedientesView(APIView):
    permission_classes = [IsAuthenticated401, IsClienteExpediente]

    def get(self, request: Request) -> Response:
        condados = _condados_cliente(request.user.idusuario)
        limit = int(request.query_params.get("limit", 20))
        data = HistorialEmergenciasService().listar(
            cursor=request.query_params.get("cursor"),
            limit=limit,
            solo_cerrados=True,
            condados_permitidos=condados,
        )
        return success_response(data)


class ClienteExpedienteDetalleView(APIView):
    permission_classes = [IsAuthenticated401, IsClienteExpediente]

    def get(self, request: Request, idaccidente: str) -> Response:
        condados = _condados_cliente(request.user.idusuario)
        data = ExpedienteService().obtener(
            idaccidente,
            condados_permitidos=condados,
            requiere_cerrado=True,
        )
        if not data:
            return error_response("not_found", "Expediente no encontrado", "404", status_code=404)
        return success_response(data)


class ClienteExpedientePdfView(APIView):
    permission_classes = [IsAuthenticated401, IsClienteExpediente]

    def get(self, request: Request, idaccidente: str) -> HttpResponse:
        condados = _condados_cliente(request.user.idusuario)
        pdf = ExpedientePdfService().generar_bytes(
            idaccidente,
            condados_permitidos=condados,
        )
        if not pdf:
            return HttpResponse(status=404)
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="expediente-{idaccidente}.pdf"'
        return response


def _condados_cliente(idusuario: int) -> set[int]:
    pinot = PinotClient()
    links = pinot.query(
        "SELECT idcliente FROM Dim_Usuario_Cliente WHERE idusuario = %(idusuario)s",
        {"idusuario": idusuario},
    )
    if not links:
        return set()
    id_cliente = links[0]["idcliente"]
    prefs = pinot.query(
        "SELECT zonas_geograficas FROM Dim_Preferencias_Cliente WHERE id_cliente = %(id_cliente)s",
        {"id_cliente": id_cliente},
    )
    if not prefs:
        return set()
    return HistorialEmergenciasService.condados_desde_preferencias(prefs[0].get("zonas_geograficas", "[]"))
