"""DRF views for RF-DES-010 algorithm parameters."""

from __future__ import annotations

from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accidentes.views.response_envelope import error_response, success_response
from apps.cuentas_clientes.permissions import IsAuthenticated401
from apps.despacho.permissions import IsDirectorTecnologicoOrAdmin
from apps.despacho.services.parametros_despacho_service import ParametrosDespachoService


class ParametrosDespachoView(APIView):
    permission_classes = [IsAuthenticated401, IsDirectorTecnologicoOrAdmin]
    parser_classes = [JSONParser]

    def get(self, request: Request) -> Response:
        data = ParametrosDespachoService().obtener()
        return success_response(data)

    def patch(self, request: Request) -> Response:
        if not request.data:
            return error_response("bad_request", "body requerido", "400", status_code=400)
        try:
            data = ParametrosDespachoService().actualizar(
                fields=request.data, idusuario=request.user.idusuario
            )
        except ValueError as exc:
            return error_response("unprocessable_entity", str(exc), "422", status_code=422)
        return success_response(data)
