"""DRF views for alta y configuración de unidades (CU-O54/56/57/58). CU-O59 eliminado."""

from __future__ import annotations

import csv
import io

from rest_framework import status
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.red_operativa.idempotency import get_cached_response, store_response
from apps.red_operativa.permissions import IsProveedorFlota
from apps.red_operativa.services.baja_unidad_service import BajaUnidadService
from apps.red_operativa.services.edicion_unidad_service import EdicionUnidadService
from apps.red_operativa.services.importacion_lote_unidad_service import (
    ImportacionLoteUnidadService,
)
from apps.red_operativa.services.proveedor_access_service import ProveedorAccessError
from apps.red_operativa.services.registro_unidad_service import RegistroUnidadService
from apps.red_operativa.services.reenviar_invitacion_unidad_service import (
    ReenviarInvitacionUnidadService,
)
from core.api.response_envelope import error_response, success_response
from core.auth.permissions import IsAuthenticated401
from core.repositories.red_operativa.unidad_emergencia_repository import (
    UnidadEmergenciaRepository,
)

def _roles(request: Request) -> list[str]:
    return list(getattr(request.user, "roles", []) or [])


class UnidadListCreateView(APIView):
    permission_classes = [IsAuthenticated401, IsProveedorFlota]
    parser_classes = [JSONParser]

    def get(self, request: Request) -> Response:
        from apps.red_operativa.services.proveedor_access_service import (
            ProveedorAccessService,
        )

        try:
            cliente = ProveedorAccessService().resolve_cliente_activo(
                user_id=request.user.idusuario,
                roles=_roles(request),
            )
        except ProveedorAccessError as exc:
            return error_response("forbidden", str(exc), "403", status_code=403)

        try:
            cursor = int(request.query_params.get("cursor") or 0)
            limit = int(request.query_params.get("limit") or 20)
        except (TypeError, ValueError):
            return error_response(
                "bad_request",
                "cursor y limit deben ser enteros",
                "400",
                status_code=400,
            )
        limit = max(1, min(limit, 100))
        q = (request.query_params.get("q") or "").strip() or None
        tipounidademergencia = (
            request.query_params.get("tipounidademergencia") or ""
        ).strip() or None
        activo_raw = request.query_params.get("activo")
        activo: bool | None = None
        if activo_raw is not None and str(activo_raw).strip() != "":
            lowered = str(activo_raw).strip().lower()
            if lowered in ("true", "1"):
                activo = True
            elif lowered in ("false", "0"):
                activo = False
            else:
                return error_response(
                    "bad_request",
                    "activo debe ser true o false",
                    "400",
                    status_code=400,
                )

        items, next_cursor = UnidadEmergenciaRepository().list_by_cliente(
            cliente["idcliente"],
            cursor=cursor,
            limit=limit,
            q=q,
            activo=activo,
            tipounidademergencia=tipounidademergencia,
        )
        return success_response(
            {"items": items},
            meta={"pagination": {"next_cursor": next_cursor, "limit": limit}},
        )

    def post(self, request: Request) -> Response:
        cached = get_cached_response(request, "unidad_create")
        if cached is not None:
            return cached
        try:
            data = RegistroUnidadService().registrar(
                dict(request.data),
                user_id=request.user.idusuario,
                roles=_roles(request),
            )
        except ProveedorAccessError as exc:
            return error_response("forbidden", str(exc), "403", status_code=403)
        except (KeyError, LookupError) as exc:
            return error_response("bad_request", str(exc), "400", status_code=400)
        except ValueError as exc:
            return error_response("conflict", str(exc), "409", status_code=409)
        body = {
            "idunidademergencia": data["idunidademergencia"],
            "placa": data["placa"],
            "activo": data["activo"],
            "idusuario": data.get("idusuario"),
            "usuario_creado": bool(data.get("usuario_creado")),
            "invitacion_enviada": bool(data.get("invitacion_enviada")),
        }
        if data.get("invitacion_error"):
            body["invitacion_error"] = data["invitacion_error"]
        response = success_response(body, status_code=status.HTTP_201_CREATED)
        store_response(request, "unidad_create", response)
        return response


class UnidadDetailView(APIView):
    permission_classes = [IsAuthenticated401, IsProveedorFlota]
    parser_classes = [JSONParser]

    def get(self, request: Request, idunidademergencia: int) -> Response:
        unidad = UnidadEmergenciaRepository().find_by_id(idunidademergencia)
        if not unidad:
            return error_response("not_found", "Unidad no encontrada", "404", status_code=404)
        try:
            from apps.red_operativa.services.proveedor_access_service import (
                ProveedorAccessService,
            )

            ProveedorAccessService().require_unidad_propia(
                user_id=request.user.idusuario,
                roles=_roles(request),
                unidad=unidad,
            )
        except ProveedorAccessError as exc:
            return error_response("forbidden", str(exc), "403", status_code=403)
        except LookupError:
            return error_response("not_found", "Unidad no encontrada", "404", status_code=404)
        return success_response(unidad)

    def patch(self, request: Request, idunidademergencia: int) -> Response:
        confirmar = str(request.query_params.get("confirmar_edicion_critica", "")).lower() == "true"
        try:
            updated = EdicionUnidadService().editar(
                idunidademergencia,
                dict(request.data),
                user_id=request.user.idusuario,
                roles=_roles(request),
                confirmar_edicion_critica=confirmar,
            )
        except ProveedorAccessError as exc:
            return error_response("forbidden", str(exc), "403", status_code=403)
        except LookupError:
            return error_response("not_found", "Unidad no encontrada", "404", status_code=404)
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
    permission_classes = [IsAuthenticated401, IsProveedorFlota]
    parser_classes = [MultiPartParser]

    def post(self, request: Request) -> Response:
        archivo = request.FILES.get("archivo")
        if not archivo:
            return error_response("bad_request", "archivo es requerido", "400", status_code=400)

        contenido = io.StringIO(archivo.read().decode("utf-8"))
        filas = list(csv.DictReader(contenido))
        for fila in filas:
            if fila.get("idcondado"):
                fila["idcondado"] = int(fila["idcondado"])
            fila.pop("idcliente", None)
            fila["activo"] = True

        try:
            resultado = ImportacionLoteUnidadService().importar(
                filas,
                user_id=request.user.idusuario,
                roles=_roles(request),
            )
        except ProveedorAccessError as exc:
            return error_response("forbidden", str(exc), "403", status_code=403)
        except ValueError as exc:
            return error_response("bad_request", str(exc), "400", status_code=400)
        return success_response(resultado)


class UnidadBajaView(APIView):
    permission_classes = [IsAuthenticated401, IsProveedorFlota]
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
                roles=_roles(request),
                forzar=forzar,
            )
        except ProveedorAccessError as exc:
            return error_response("forbidden", str(exc), "403", status_code=403)
        except LookupError:
            return error_response("not_found", "Unidad no encontrada", "404", status_code=404)
        except ValueError as exc:
            return error_response("conflict", str(exc), "409", status_code=409)
        return success_response(data)


class UnidadReactivarView(APIView):
    permission_classes = [IsAuthenticated401, IsProveedorFlota]

    def post(self, request: Request, idunidademergencia: int) -> Response:
        try:
            data = BajaUnidadService().reactivar(
                idunidademergencia,
                user_id=request.user.idusuario,
                roles=_roles(request),
            )
        except ProveedorAccessError as exc:
            return error_response("forbidden", str(exc), "403", status_code=403)
        except LookupError:
            return error_response("not_found", "Unidad no encontrada", "404", status_code=404)
        except ValueError as exc:
            return error_response("conflict", str(exc), "409", status_code=409)
        return success_response(data)


class UnidadInvitacionReenviarView(APIView):
    permission_classes = [IsAuthenticated401, IsProveedorFlota]

    def post(self, request: Request, idunidademergencia: int) -> Response:
        try:
            data = ReenviarInvitacionUnidadService().reenviar(
                idunidademergencia,
                user_id=request.user.idusuario,
                roles=_roles(request),
            )
        except ProveedorAccessError as exc:
            return error_response("forbidden", str(exc), "403", status_code=403)
        except LookupError:
            return error_response("not_found", "Unidad no encontrada", "404", status_code=404)
        except ValueError as exc:
            return error_response("conflict", str(exc), "409", status_code=409)
        return success_response(data)
