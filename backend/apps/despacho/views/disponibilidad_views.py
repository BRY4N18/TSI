"""DRF views for disponibilidad de unidad."""

from __future__ import annotations

from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accidentes.services.audit_evidencia_service import AuditEvidenciaService
from core.api.response_envelope import error_response, success_response
from apps.cuentas_clientes.permissions import IsAuthenticated401
from apps.despacho.permissions import (
    IsAdministradorOrDespachoService,
    IsUnidadEmergenciaOwn,
    IsUnidadEmergenciaSelfOrAdmin,
)
from apps.despacho.services.consulta_flota_service import ConsultaFlotaService
from apps.despacho.services.disponibilidad_unidad_service import DisponibilidadUnidadService


class MiDisponibilidadView(APIView):
    permission_classes = [IsAuthenticated401, IsUnidadEmergenciaOwn]
    parser_classes = [JSONParser]

    def get(self, request: Request) -> Response:
        try:
            data = DisponibilidadUnidadService().consultar_por_usuario(request.user.idusuario)
        except LookupError:
            return error_response("forbidden", "Unidad no vinculada", "403", status_code=403)
        return success_response(data)

    def post(self, request: Request) -> Response:
        estadonuevo = request.data.get("estadonuevo")
        if not estadonuevo:
            return error_response("bad_request", "estadonuevo requerido", "400", status_code=400)
        try:
            data = DisponibilidadUnidadService().declarar_estado_por_usuario(
                idusuario=request.user.idusuario,
                estadonuevo=str(estadonuevo),
            )
            AuditEvidenciaService().log_cambio_disponibilidad(
                user_id=request.user.idusuario,
                idunidademergencia=data["idunidademergencia"],
                estadoanterior=data["estadoanterior"],
                estadonuevo=data["estadonuevo"],
            )
        except LookupError:
            return error_response("forbidden", "Unidad no vinculada", "403", status_code=403)
        except ValueError as exc:
            return error_response("unprocessable_entity", str(exc), "422", status_code=422)
        return success_response(data, status_code=status.HTTP_201_CREATED)


class UnidadesEmergenciaListView(APIView):
    permission_classes = [IsAuthenticated401, IsAdministradorOrDespachoService]

    def get(self, request: Request) -> Response:
        limit = min(int(request.query_params.get("limit", 20)), 100)
        cursor = request.query_params.get("cursor")
        cursor_int = int(cursor) if cursor else None
        estado = request.query_params.get("estado")
        idtipounidad = request.query_params.get("idtipounidad")
        items, next_cursor = ConsultaFlotaService().listar(
            estado=estado,
            idtipounidad=int(idtipounidad) if idtipounidad else None,
            limit=limit,
            cursor=cursor_int,
        )
        return success_response(
            {"items": items},
            meta={"pagination": {"next_cursor": next_cursor, "limit": limit}},
        )


class UnidadDisponibilidadView(APIView):
    permission_classes = [IsAuthenticated401, IsUnidadEmergenciaSelfOrAdmin]

    def get(self, request: Request, idunidademergencia: int) -> Response:
        try:
            data = DisponibilidadUnidadService().consultar(idunidademergencia)
        except LookupError:
            return error_response("not_found", "Unidad no encontrada", "404", status_code=404)
        return success_response(data)


class UnidadHistorialEstadoView(APIView):
    permission_classes = [IsAuthenticated401, IsUnidadEmergenciaSelfOrAdmin]
    parser_classes = [JSONParser]

    def get(self, request: Request, idunidademergencia: int) -> Response:
        limit = min(int(request.query_params.get("limit", 20)), 100)
        cursor = request.query_params.get("cursor")
        cursor_int = int(cursor) if cursor else None
        try:
            items, next_cursor = DisponibilidadUnidadService().listar_historial(
                idunidademergencia,
                limit=limit,
                cursor=cursor_int,
            )
        except LookupError:
            return error_response("not_found", "Unidad no encontrada", "404", status_code=404)
        return success_response(
            {"items": items},
            meta={"pagination": {"next_cursor": next_cursor, "limit": limit}},
        )

    def post(self, request: Request, idunidademergencia: int) -> Response:
        estadonuevo = request.data.get("estadonuevo")
        if not estadonuevo:
            return error_response("bad_request", "estadonuevo requerido", "400", status_code=400)
        try:
            data = DisponibilidadUnidadService().declarar_estado(
                idunidademergencia=idunidademergencia,
                estadonuevo=str(estadonuevo),
                idusuario=request.user.idusuario,
            )
            AuditEvidenciaService().log_cambio_disponibilidad(
                user_id=request.user.idusuario,
                idunidademergencia=idunidademergencia,
                estadoanterior=data["estadoanterior"],
                estadonuevo=data["estadonuevo"],
            )
        except LookupError:
            return error_response("not_found", "Unidad no encontrada", "404", status_code=404)
        except ValueError as exc:
            return error_response("unprocessable_entity", str(exc), "422", status_code=422)
        return success_response(data, status_code=status.HTTP_201_CREATED)
