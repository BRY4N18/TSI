"""DRF views for /mi-seguimiento/* (CU-O25, O26, O39)."""

from __future__ import annotations

from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.despacho.consumers.despacho_abortado_consumer import handle_despacho_abortado
from apps.seguimiento.idempotency import get_cached_response, store_response
from apps.seguimiento.permissions import IsUnidadSeguimiento
from apps.seguimiento.services.abortar_mision_service import AbortarMisionService
from apps.seguimiento.services.obtener_mi_seguimiento_actual_service import (
    ObtenerMiSeguimientoActualService,
)
from apps.seguimiento.services.registrar_llegada_service import RegistrarLlegadaService
from apps.seguimiento.services.registrar_posicion_gps_service import (
    RegistrarPosicionGpsService,
)
from core.api.response_envelope import error_response, success_response
from core.auth.permissions import IsAuthenticated401
from core.repositories.despacho.unidad_emergencia_repository import (
    UnidadEmergenciaRepository,
)


class MiSeguimientoActualView(APIView):
    permission_classes = [IsAuthenticated401, IsUnidadSeguimiento]

    def get(self, request: Request) -> Response:
        unidad = UnidadEmergenciaRepository().find_by_usuario(request.user.idusuario)
        if not unidad:
            return error_response("forbidden", "Unidad no vinculada", "403", status_code=403)
        despacho = ObtenerMiSeguimientoActualService().obtener(
            idunidademergencia=int(unidad["idunidademergencia"]),
        )
        return success_response({"despacho": despacho})


class RegistrarPosicionGpsView(APIView):
    permission_classes = [IsAuthenticated401, IsUnidadSeguimiento]
    parser_classes = [JSONParser]

    def post(self, request: Request) -> Response:
        cached = get_cached_response(request, "registrar_posicion")
        if cached is not None:
            return cached
        data = request.data
        required = ("idunidademergencia", "idaccidente", "latitud", "longitud", "fechahora")
        if not all(k in data for k in required):
            return error_response("bad_request", "Campos GPS requeridos", "400", status_code=400)
        unidad = UnidadEmergenciaRepository().find_by_usuario(request.user.idusuario)
        if not unidad or int(unidad["idunidademergencia"]) != int(data["idunidademergencia"]):
            return error_response("forbidden", "Unidad no vinculada", "403", status_code=403)
        try:
            result = RegistrarPosicionGpsService().registrar(
                idunidademergencia=int(data["idunidademergencia"]),
                idaccidente=str(data["idaccidente"]),
                latitud=float(data["latitud"]),
                longitud=float(data["longitud"]),
                fechahora=int(data["fechahora"]),
                idusuario=request.user.idusuario,
            )
        except ValueError as exc:
            return error_response("conflict", str(exc), "409", status_code=409)
        response = success_response(result, status_code=202)
        store_response(request, "registrar_posicion", response)
        return response


class RegistrarLlegadaView(APIView):
    permission_classes = [IsAuthenticated401, IsUnidadSeguimiento]

    def post(self, request: Request, iddespacho: int) -> Response:
        cached = get_cached_response(request, "registrar_llegada")
        if cached is not None:
            return cached
        unidad = UnidadEmergenciaRepository().find_by_usuario(request.user.idusuario)
        if not unidad:
            return error_response("forbidden", "Unidad no vinculada", "403", status_code=403)
        try:
            data = RegistrarLlegadaService().registrar(
                iddespacho=iddespacho,
                idunidademergencia=int(unidad["idunidademergencia"]),
                idusuario=request.user.idusuario,
            )
        except PermissionError:
            return error_response("forbidden", "Despacho no pertenece a la unidad", "403", status_code=403)
        except LookupError:
            return error_response("not_found", "Despacho no encontrado", "404", status_code=404)
        except ValueError as exc:
            return error_response("conflict", str(exc), "409", status_code=409)
        response = success_response(data)
        store_response(request, "registrar_llegada", response)
        return response


class AbortarMisionView(APIView):
    permission_classes = [IsAuthenticated401, IsUnidadSeguimiento]
    parser_classes = [JSONParser]

    def post(self, request: Request, iddespacho: int) -> Response:
        cached = get_cached_response(request, "abortar_mision")
        if cached is not None:
            return cached
        unidad = UnidadEmergenciaRepository().find_by_usuario(request.user.idusuario)
        if not unidad:
            return error_response("forbidden", "Unidad no vinculada", "403", status_code=403)
        try:
            result = AbortarMisionService().abortar(
                iddespacho=iddespacho,
                idunidademergencia=int(unidad["idunidademergencia"]),
                idusuario=request.user.idusuario,
                motivo=request.data.get("motivo"),
            )
            handle_despacho_abortado(
                {
                    "iddespacho": iddespacho,
                    "idaccidente": result["idaccidente"],
                    "idusuario": request.user.idusuario,
                }
            )
        except PermissionError:
            return error_response("forbidden", "Despacho no pertenece a la unidad", "403", status_code=403)
        except LookupError:
            return error_response("not_found", "Despacho no encontrado", "404", status_code=404)
        except ValueError as exc:
            return error_response("conflict", str(exc), "409", status_code=409)
        response = success_response(result)
        store_response(request, "abortar_mision", response)
        return response
