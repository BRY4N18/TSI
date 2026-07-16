"""DRF views for accidente actions."""

from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accidentes.permissions import OperadorEmergenciasPermission, UnidadEmergenciaPermission
from apps.accidentes.services.confirmar_reporte_service import ConfirmarReporteService, ConflictError
from apps.accidentes.services.descartar_caso_service import DescartarCasoService
from apps.accidentes.services.escalar_severidad_service import EscalarSeveridadService
from apps.accidentes.services.fusionar_reportes_service import FusionarReportesService
from core.api.response_envelope import error_response, success_response
from apps.cuentas_clientes.permissions import IsAuthenticated401


class ConfirmarReporteView(APIView):
    permission_classes = [IsAuthenticated401, OperadorEmergenciasPermission]

    def post(self, request: Request, idaccidente: str) -> Response:
        try:
            data = ConfirmarReporteService().confirmar(
                idaccidente=idaccidente,
                idusuario=request.user.idusuario,
                confirmacion=bool(request.data.get("confirmacion")),
            )
        except ConflictError as exc:
            return error_response("conflict", str(exc), "409", status_code=409)
        except ValueError as exc:
            return error_response("bad_request", str(exc), "400", status_code=400)
        return success_response(data)


class DescartarCasoView(APIView):
    permission_classes = [IsAuthenticated401, OperadorEmergenciasPermission]

    def post(self, request: Request, idaccidente: str) -> Response:
        try:
            data = DescartarCasoService().descartar(
                idaccidente=idaccidente,
                idusuario=request.user.idusuario,
                motivo=request.data.get("motivo"),
            )
        except ConflictError as exc:
            return error_response("conflict", str(exc), "409", status_code=409)
        return success_response(data)


class FusionarReportesView(APIView):
    permission_classes = [IsAuthenticated401, OperadorEmergenciasPermission]

    def post(self, request: Request, idaccidente: str) -> Response:
        try:
            data = FusionarReportesService().fusionar(
                idaccidente_duplicado=idaccidente,
                idaccidente_principal=request.data["idaccidenteprincipal"],
                idusuario=request.user.idusuario,
                confirmacion=bool(request.data.get("confirmacion")),
            )
        except ConflictError as exc:
            return error_response("conflict", str(exc), "409", status_code=409)
        except (KeyError, ValueError) as exc:
            return error_response("bad_request", str(exc), "400", status_code=400)
        return success_response(data)


class EscalarSeveridadView(APIView):
    permission_classes = [IsAuthenticated401, UnidadEmergenciaPermission]

    def post(self, request: Request, idaccidente: str) -> Response:
        try:
            data = EscalarSeveridadService().escalar(
                idaccidente=idaccidente,
                data=request.data,
                idusuario=request.user.idusuario,
            )
        except ConflictError as exc:
            return error_response("conflict", str(exc), "409", status_code=409)
        except LookupError:
            return error_response("not_found", "Accidente no encontrado", "404", status_code=404)
        except ValueError as exc:
            return error_response("unprocessable_entity", str(exc), "422", status_code=422)
        except KeyError as exc:
            return error_response("bad_request", f"Campo requerido: {exc}", "400", status_code=400)
        return success_response(data)
