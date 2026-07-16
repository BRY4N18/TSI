"""Vistas historial operador (CU-O29)."""

from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.response_envelope import error_response, success_response
from apps.cuentas_clientes.permissions import IsAuthenticated401
from apps.seguimiento.permissions import IsOperadorSeguimiento
from apps.seguimiento.services.expediente_service import ExpedienteService
from apps.seguimiento.services.historial_emergencias_service import HistorialEmergenciasService


class HistorialEmergenciasView(APIView):
    permission_classes = [IsAuthenticated401, IsOperadorSeguimiento]

    def get(self, request: Request) -> Response:
        params = request.query_params
        limit = int(params.get("limit", 20))
        try:
            data = HistorialEmergenciasService().listar(
                cursor=params.get("cursor"),
                limit=limit,
                estado=params.get("estado"),
                idseveridad=int(params["idseveridad"]) if params.get("idseveridad") else None,
                idunidademergencia=int(params["idunidademergencia"])
                if params.get("idunidademergencia")
                else None,
                fecha_desde=int(params["fecha_desde"]) if params.get("fecha_desde") else None,
                fecha_hasta=int(params["fecha_hasta"]) if params.get("fecha_hasta") else None,
                idciudad=int(params["idciudad"]) if params.get("idciudad") else None,
                idestadoregion=int(params["idestadoregion"]) if params.get("idestadoregion") else None,
            )
        except ValueError:
            return error_response("bad_request", "Parámetros de filtro inválidos", "400", status_code=400)
        return success_response(data)


class ExpedienteOperadorView(APIView):
    permission_classes = [IsAuthenticated401, IsOperadorSeguimiento]

    def get(self, request: Request, idaccidente: str) -> Response:
        data = ExpedienteService().obtener(idaccidente)
        if not data:
            return error_response("not_found", "Expediente no encontrado", "404", status_code=404)
        return success_response(data)
