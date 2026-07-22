"""DRF views for alta y configuración de unidades de emergencia (CU-O54/56/57/58/59)."""

from __future__ import annotations

import csv
import io

from rest_framework import status
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.red_operativa.permissions import (
    IsAdministradorOrOperador,
    IsAdministradorRedOperativa,
    IsOperadorDisponibilidadExterna,
)
from apps.red_operativa.services.baja_unidad_service import BajaUnidadService
from apps.red_operativa.services.disponibilidad_externa_service import (
    DisponibilidadExternaService,
)
from apps.red_operativa.services.edicion_unidad_service import EdicionUnidadService
from apps.red_operativa.services.importacion_lote_unidad_service import (
    ImportacionLoteUnidadService,
)
from apps.red_operativa.services.registro_unidad_service import RegistroUnidadService
from core.api.response_envelope import error_response, success_response
from core.auth.permissions import IsAuthenticated401
from core.repositories.red_operativa.unidad_emergencia_repository import (
    UnidadEmergenciaRepository,
)


class UnidadListCreateView(APIView):
    permission_classes = [IsAuthenticated401, IsAdministradorRedOperativa]
    parser_classes = [JSONParser]

    def post(self, request: Request) -> Response:
        try:
            data = RegistroUnidadService().registrar(dict(request.data))
        except (KeyError, LookupError) as exc:
            return error_response("bad_request", str(exc), "400", status_code=400)
        except ValueError as exc:
            return error_response("conflict", str(exc), "409", status_code=409)
        return success_response(
            {
                "idunidademergencia": data["idunidademergencia"],
                "placa": data["placa"],
                "activo": data["activo"],
            },
            status_code=status.HTTP_201_CREATED,
        )


class UnidadDetailView(APIView):
    permission_classes = [IsAuthenticated401, IsAdministradorOrOperador]
    parser_classes = [JSONParser]

    def get(self, request: Request, idunidademergencia: int) -> Response:
        unidad = UnidadEmergenciaRepository().find_by_id(idunidademergencia)
        if not unidad:
            return error_response("not_found", "Unidad no encontrada", "404", status_code=404)
        return success_response(unidad)

    def patch(self, request: Request, idunidademergencia: int) -> Response:
        if "Administrador" not in getattr(request.user, "roles", []):
            return error_response(
                "forbidden", "Solo el Administrador puede editar unidades", "403", status_code=403
            )
        confirmar = str(request.query_params.get("confirmar_edicion_critica", "")).lower() == "true"
        try:
            updated = EdicionUnidadService().editar(
                idunidademergencia,
                dict(request.data),
                confirmar_edicion_critica=confirmar,
            )
        except KeyError as exc:
            return error_response("bad_request", str(exc), "400", status_code=400)
        except ValueError as exc:
            return error_response("conflict", str(exc), "409", status_code=409)
        if updated is None:
            return error_response("not_found", "Unidad no encontrada", "404", status_code=404)
        campos_modificados = [k for k in request.data.keys() if k in updated]
        return success_response(
            {"idunidademergencia": idunidademergencia, "campos_modificados": campos_modificados}
        )


class UnidadImportacionLoteView(APIView):
    permission_classes = [IsAuthenticated401, IsAdministradorRedOperativa]
    parser_classes = [MultiPartParser]

    def post(self, request: Request) -> Response:
        archivo = request.FILES.get("archivo")
        if not archivo:
            return error_response("bad_request", "archivo es requerido", "400", status_code=400)

        contenido = io.StringIO(archivo.read().decode("utf-8"))
        filas = list(csv.DictReader(contenido))
        for fila in filas:
            for campo in ("idcliente", "idcondado"):
                if fila.get(campo):
                    fila[campo] = int(fila[campo])
            fila["activo"] = True

        try:
            resultado = ImportacionLoteUnidadService().importar(filas)
        except ValueError as exc:
            return error_response("bad_request", str(exc), "400", status_code=400)
        return success_response(resultado)


class UnidadBajaView(APIView):
    permission_classes = [IsAuthenticated401, IsAdministradorRedOperativa]
    parser_classes = [JSONParser]

    def post(self, request: Request, idunidademergencia: int) -> Response:
        motivo = request.data.get("motivo")
        if not motivo:
            return error_response("bad_request", "motivo es requerido", "400", status_code=400)
        forzar = bool(request.data.get("forzar", False))
        try:
            data = BajaUnidadService().dar_de_baja(
                idunidademergencia,
                motivo=str(motivo),
                idusuario=request.user.idusuario,
                forzar=forzar,
            )
        except LookupError:
            return error_response("not_found", "Unidad no encontrada", "404", status_code=404)
        except ValueError as exc:
            return error_response("conflict", str(exc), "409", status_code=409)
        return success_response(data)


class UnidadReactivarView(APIView):
    permission_classes = [IsAuthenticated401, IsAdministradorRedOperativa]

    def post(self, request: Request, idunidademergencia: int) -> Response:
        try:
            data = BajaUnidadService().reactivar(idunidademergencia)
        except LookupError:
            return error_response("not_found", "Unidad no encontrada", "404", status_code=404)
        except ValueError as exc:
            return error_response("conflict", str(exc), "409", status_code=409)
        return success_response(data)


class UnidadDisponibilidadView(APIView):
    permission_classes = [IsAuthenticated401, IsOperadorDisponibilidadExterna]
    parser_classes = [JSONParser]

    def post(self, request: Request, idunidademergencia: int) -> Response:
        estadonuevo = request.data.get("estadonuevo") or request.data.get(
            "idestadounidademergencia"
        )
        if not estadonuevo:
            return error_response("bad_request", "estadonuevo requerido", "400", status_code=400)
        try:
            data = DisponibilidadExternaService().declarar(
                idunidademergencia=idunidademergencia,
                estadonuevo=str(estadonuevo),
                idusuario_operador=request.user.idusuario,
            )
        except PermissionError as exc:
            return error_response("bad_request", str(exc), "400", status_code=400)
        except ValueError as exc:
            return error_response("unprocessable_entity", str(exc), "422", status_code=422)
        return success_response(
            {"idunidademergencia": idunidademergencia, "estadonuevo": data["estadonuevo"]}
        )
