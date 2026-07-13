"""DRF views for /mi-despacho/* (CU-O24, CU-O45)."""

from __future__ import annotations

from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accidentes.views.response_envelope import error_response, success_response
from apps.cuentas_clientes.permissions import IsAuthenticated401
from apps.despacho.permissions import IsUnidadDespachoOwn
from apps.despacho.services.confirmar_despacho_service import ConfirmarDespachoService
from apps.despacho.services.mi_despacho_service import MiDespachoService
from apps.despacho.services.rechazar_despacho_service import RechazarDespachoService
from core.repositories.despacho.unidad_emergencia_repository import UnidadEmergenciaRepository


class MiDespachoPendientesView(APIView):
    permission_classes = [IsAuthenticated401, IsUnidadDespachoOwn]

    def get(self, request: Request) -> Response:
        try:
            items = MiDespachoService().listar_pendientes(idusuario=request.user.idusuario)
        except LookupError:
            return error_response("forbidden", "Unidad no vinculada", "403", status_code=403)
        return success_response({"pendientes": items})


class MiDespachoDetalleView(APIView):
    permission_classes = [IsAuthenticated401, IsUnidadDespachoOwn]

    def get(self, request: Request, idnotificaciondespacho: int) -> Response:
        unidad = UnidadEmergenciaRepository().find_by_usuario(request.user.idusuario)
        if not unidad:
            return error_response("forbidden", "Unidad no vinculada", "403", status_code=403)
        try:
            data = MiDespachoService().obtener_detalle(
                idnotificaciondespacho=idnotificaciondespacho,
                idunidademergencia=int(unidad["idunidademergencia"]),
            )
        except PermissionError:
            return error_response("forbidden", "Notificación no pertenece a la unidad", "403", status_code=403)
        except LookupError:
            return error_response("not_found", "Notificación no encontrada", "404", status_code=404)
        return success_response(data)


class MiDespachoConfirmarView(APIView):
    permission_classes = [IsAuthenticated401, IsUnidadDespachoOwn]

    def post(self, request: Request, idnotificaciondespacho: int) -> Response:
        unidad = UnidadEmergenciaRepository().find_by_usuario(request.user.idusuario)
        if not unidad:
            return error_response("forbidden", "Unidad no vinculada", "403", status_code=403)
        try:
            data = ConfirmarDespachoService().confirmar(
                idnotificaciondespacho=idnotificaciondespacho,
                idunidademergencia=int(unidad["idunidademergencia"]),
                idusuario=request.user.idusuario,
            )
        except PermissionError:
            return error_response("forbidden", "Notificación no pertenece a la unidad", "403", status_code=403)
        except LookupError:
            return error_response("not_found", "Notificación no encontrada", "404", status_code=404)
        except ValueError as exc:
            return error_response("conflict", str(exc), "409", status_code=409)
        return success_response(data)


class MiDespachoRechazarView(APIView):
    permission_classes = [IsAuthenticated401, IsUnidadDespachoOwn]
    parser_classes = [JSONParser]

    def post(self, request: Request, idnotificaciondespacho: int) -> Response:
        motivo = request.data.get("motivo")
        if not motivo or not str(motivo).strip():
            return error_response("bad_request", "motivo requerido", "400", status_code=400)
        unidad = UnidadEmergenciaRepository().find_by_usuario(request.user.idusuario)
        if not unidad:
            return error_response("forbidden", "Unidad no vinculada", "403", status_code=403)
        try:
            data = RechazarDespachoService().rechazar(
                idnotificaciondespacho=idnotificaciondespacho,
                idunidademergencia=int(unidad["idunidademergencia"]),
                motivo=str(motivo).strip(),
                idusuario=request.user.idusuario,
            )
        except PermissionError:
            return error_response("forbidden", "Notificación no pertenece a la unidad", "403", status_code=403)
        except LookupError:
            return error_response("not_found", "Notificación no encontrada", "404", status_code=404)
        except ValueError as exc:
            return error_response("conflict", str(exc), "409", status_code=409)
        return success_response(data)
