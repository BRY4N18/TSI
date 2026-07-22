"""DRF views for the cascading location catalog (RF-REG-006 punto 3, Escenario 5)."""

from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accidentes.permissions import AccidentesLecturaPermission
from apps.accidentes.services.ubicacion_catalogo_service import UbicacionCatalogoService
from core.api.response_envelope import error_response, success_response
from core.auth.permissions import IsAuthenticated401


def _parse_required_int(request: Request, param: str) -> int | None:
    try:
        return int(request.query_params[param])
    except (KeyError, ValueError, TypeError):
        return None


class PaisListView(APIView):
    permission_classes = [IsAuthenticated401, AccidentesLecturaPermission]

    def get(self, request: Request) -> Response:
        return success_response(UbicacionCatalogoService().listar_paises())


class EstadoListView(APIView):
    permission_classes = [IsAuthenticated401, AccidentesLecturaPermission]

    def get(self, request: Request) -> Response:
        idpais = _parse_required_int(request, "idpais")
        if idpais is None:
            return error_response("bad_request", "idpais requerido", "400", status_code=400)
        return success_response(UbicacionCatalogoService().listar_estados(idpais))


class CondadoListView(APIView):
    permission_classes = [IsAuthenticated401, AccidentesLecturaPermission]

    def get(self, request: Request) -> Response:
        idestado = _parse_required_int(request, "idestado")
        if idestado is None:
            return error_response("bad_request", "idestado requerido", "400", status_code=400)
        return success_response(UbicacionCatalogoService().listar_condados(idestado))


class CiudadListView(APIView):
    permission_classes = [IsAuthenticated401, AccidentesLecturaPermission]

    def get(self, request: Request) -> Response:
        idcondado = _parse_required_int(request, "idcondado")
        if idcondado is None:
            return error_response("bad_request", "idcondado requerido", "400", status_code=400)
        return success_response(UbicacionCatalogoService().listar_ciudades(idcondado))


class CalleListView(APIView):
    permission_classes = [IsAuthenticated401, AccidentesLecturaPermission]

    def get(self, request: Request) -> Response:
        idciudad = _parse_required_int(request, "idciudad")
        if idciudad is None:
            return error_response("bad_request", "idciudad requerido", "400", status_code=400)
        return success_response(UbicacionCatalogoService().listar_calles(idciudad))
