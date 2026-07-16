"""DRF views for operator assignment actions (O33, O34, O38)."""

from __future__ import annotations

from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.response_envelope import error_response, success_response
from apps.cuentas_clientes.permissions import IsAuthenticated401
from apps.despacho.permissions import IsOperadorDespacho
from apps.despacho.services.asignacion_manual_service import AsignacionManualService
from apps.despacho.services.consulta_candidatas_service import ConsultaCandidatasService
from apps.despacho.services.coordinacion_multiple_service import CoordinacionMultipleService
from apps.despacho.services.escalamiento_zona_service import EscalamientoZonaService
from rest_framework import status


class UnidadesCandidatasView(APIView):
    permission_classes = [IsAuthenticated401, IsOperadorDespacho]

    def get(self, request: Request, idaccidente: str) -> Response:
        incluir_vecinos = request.query_params.get("incluir_vecinos", "false").lower() == "true"
        try:
            candidatas = ConsultaCandidatasService().listar_puntuadas(
                idaccidente, incluir_vecinos=incluir_vecinos
            )
        except LookupError:
            return error_response("not_found", "Accidente no encontrado", "404", status_code=404)
        return success_response(
            {
                "idaccidente": idaccidente,
                "incluye_vecinos": incluir_vecinos,
                "candidatas": candidatas,
            }
        )


class AsignarManualView(APIView):
    permission_classes = [IsAuthenticated401, IsOperadorDespacho]
    parser_classes = [JSONParser]

    def post(self, request: Request, idaccidente: str) -> Response:
        idunidad = request.data.get("idunidademergencia")
        if idunidad is None:
            return error_response("bad_request", "idunidademergencia requerido", "400", status_code=400)
        try:
            data = AsignacionManualService().asignar(
                idaccidente=idaccidente,
                idunidademergencia=int(idunidad),
                idusuario=request.user.idusuario,
            )
        except LookupError:
            return error_response("not_found", "Accidente no encontrado", "404", status_code=404)
        except ValueError as exc:
            msg = str(exc)
            code = 409 if "no disponible" in msg.lower() or "ya asignada" in msg.lower() else 422
            return error_response("conflict" if code == 409 else "unprocessable_entity", msg, str(code), status_code=code)
        return success_response(data, status_code=status.HTTP_201_CREATED)


class EscalarZonaView(APIView):
    permission_classes = [IsAuthenticated401, IsOperadorDespacho]

    def post(self, request: Request, idaccidente: str) -> Response:
        try:
            data = EscalamientoZonaService().escalar(
                idaccidente=idaccidente, idusuario=request.user.idusuario
            )
        except LookupError:
            return error_response("not_found", "Accidente no encontrado", "404", status_code=404)
        if data.get("alerta_registrada"):
            return success_response(data, status_code=status.HTTP_202_ACCEPTED)
        return success_response(data, status_code=status.HTTP_200_OK)


class CoordinarDespachoView(APIView):
    permission_classes = [IsAuthenticated401, IsOperadorDespacho]
    parser_classes = [JSONParser]

    def post(self, request: Request, idaccidente: str) -> Response:
        idunidad = request.data.get("idunidademergencia")
        if idunidad is None:
            return error_response("bad_request", "idunidademergencia requerido", "400", status_code=400)
        try:
            data = CoordinacionMultipleService().coordinar(
                idaccidente=idaccidente,
                idunidademergencia=int(idunidad),
                idusuario=request.user.idusuario,
            )
        except LookupError:
            return error_response("not_found", "Accidente no encontrado", "404", status_code=404)
        except ValueError as exc:
            return error_response("conflict", str(exc), "409", status_code=409)
        return success_response(data, status_code=status.HTTP_201_CREATED)
