"""Vistas cierre, cancelación y forzar retiro."""

from __future__ import annotations

from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.seguimiento.permissions import IsOperadorSeguimiento
from apps.seguimiento.services.cancelar_caso_service import CancelarCasoService
from apps.seguimiento.services.cerrar_caso_service import CerrarCasoService
from apps.seguimiento.services.forzar_retiro_service import ForzarRetiroService
from core.api.response_envelope import error_response, success_response
from core.auth.permissions import IsAuthenticated401


class CerrarCasoView(APIView):
    permission_classes = [IsAuthenticated401, IsOperadorSeguimiento]
    parser_classes = [JSONParser]

    def post(self, request: Request, idaccidente: str) -> Response:
        if "resultado_atencion" not in request.data:
            return error_response("bad_request", "resultado_atencion requerido", "400", status_code=400)
        try:
            data = CerrarCasoService().cerrar(
                idaccidente=idaccidente,
                idusuario=request.user.idusuario,
                payload=request.data,
            )
        except LookupError:
            return error_response("not_found", "Accidente no encontrado", "404", status_code=404)
        except ValueError as exc:
            return error_response("conflict", str(exc), "409", status_code=409)
        return success_response(data)


class CancelarCasoView(APIView):
    permission_classes = [IsAuthenticated401, IsOperadorSeguimiento]
    parser_classes = [JSONParser]

    def post(self, request: Request, idaccidente: str) -> Response:
        motivo = request.data.get("motivo")
        if not motivo:
            return error_response("bad_request", "motivo requerido", "400", status_code=400)
        try:
            data = CancelarCasoService().cancelar(
                idaccidente=idaccidente,
                idusuario=request.user.idusuario,
                motivo=str(motivo),
            )
        except LookupError:
            return error_response("not_found", "Accidente no encontrado", "404", status_code=404)
        except ValueError as exc:
            return error_response("conflict", str(exc), "409", status_code=409)
        return success_response(data)


class ForzarRetiroView(APIView):
    permission_classes = [IsAuthenticated401, IsOperadorSeguimiento]

    def post(self, request: Request, iddespacho: int) -> Response:
        try:
            data = ForzarRetiroService().forzar(
                iddespacho=iddespacho,
                idusuario=request.user.idusuario,
            )
        except LookupError:
            return error_response("not_found", "Despacho no encontrado", "404", status_code=404)
        except ValueError as exc:
            return error_response("conflict", str(exc), "409", status_code=409)
        return success_response(data)
