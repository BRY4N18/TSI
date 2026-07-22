"""DRF views for accidentes CRUD and geocoding."""

from __future__ import annotations

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accidentes.permissions import (
    AccidentesLecturaPermission,
    OperadorEmergenciasPermission,
)
from apps.accidentes.services.consulta_accidente_service import ConsultaAccidenteService
from apps.accidentes.services.geocodificacion_inversa_service import (
    GeocodificacionInversaService,
)
from apps.accidentes.services.registro_accidente_service import (
    BlockingValidationError,
    DuplicateConflictError,
    RegistroAccidenteService,
)
from core.api.response_envelope import error_response, success_response
from core.auth.permissions import IsAuthenticated401


class GeocodificacionInversaView(APIView):
    permission_classes = [IsAuthenticated401, OperadorEmergenciasPermission]

    def get(self, request: Request) -> Response:
        try:
            lat = float(request.query_params["latitud"])
            lon = float(request.query_params["longitud"])
        except (KeyError, ValueError, TypeError):
            return error_response("bad_request", "latitud y longitud requeridas", "400", status_code=400)
        data = GeocodificacionInversaService().sugerir(lat, lon)
        return success_response(data)


class AccidenteListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated401(), OperadorEmergenciasPermission()]
        return [IsAuthenticated401(), AccidentesLecturaPermission()]

    def get(self, request: Request) -> Response:
        params = request.query_params
        idseveridad = params.get("idseveridad")
        fecha_desde = params.get("fecha_desde")
        fecha_hasta = params.get("fecha_hasta")
        idciudad = params.get("idciudad")
        idestadoregion = params.get("idestadoregion")
        activo = params.get("activo")
        try:
            rows = ConsultaAccidenteService().listar(
                idseveridad=int(idseveridad) if idseveridad else None,
                estado=params.get("estado") or None,
                activo=activo.lower() == "true" if activo is not None else True,
                fecha_desde=int(fecha_desde) if fecha_desde else None,
                fecha_hasta=int(fecha_hasta) if fecha_hasta else None,
                idciudad=int(idciudad) if idciudad else None,
                idestadoregion=int(idestadoregion) if idestadoregion else None,
                limit=int(params.get("limit", 20)),
            )
        except ValueError:
            return error_response("bad_request", "Parámetros de filtro inválidos", "400", status_code=400)
        return success_response(rows, meta={"pagination": {"next_cursor": None, "limit": 20}})

    def post(self, request: Request) -> Response:
        forzar = request.query_params.get("forzarAdvertencias", "false").lower() == "true"
        try:
            data = RegistroAccidenteService().registrar(
                request.data,
                idusuario=request.user.idusuario,
                forzar_advertencias=forzar,
            )
        except DuplicateConflictError as exc:
            dup_id = exc.candidates[0]["idaccidente"] if exc.candidates else None
            primera_advertencia = exc.advertencias[0] if exc.advertencias else {}
            # No usa error_response(): el frontend (registro-accidente.page.ts)
            # depende del detalle del conflicto anidado en `data` (advertencias,
            # idaccidente_similar) para abrir el diálogo de fusión — un shape
            # distinto al envelope error/detail/code de nivel raíz. Ver fix G4/G6
            # en .specify/docs/changelog.md.
            return Response(
                {
                    "data": {
                        "error": primera_advertencia.get("code", "duplicado_posible"),
                        "detail": primera_advertencia.get("detail", "Posible duplicado detectado"),
                        "code": "409",
                        "advertencias": exc.advertencias,
                        "idaccidente_similar": dup_id,
                        "idaccidente_principal_sugerido": exc.parent_suggested,
                        "idaccidente_duplicado_sugerido": None,
                    },
                    "meta": {"pagination": None},
                },
                status=status.HTTP_409_CONFLICT,
            )
        except BlockingValidationError as exc:
            error_code = "bad_request" if exc.status_code == 400 else "unprocessable_entity"
            return error_response(error_code, exc.detail, str(exc.status_code), status_code=exc.status_code)
        return success_response(data, status_code=status.HTTP_201_CREATED)


class AccidenteDetailView(APIView):
    def get_permissions(self):
        if self.request.method == "PATCH":
            return [IsAuthenticated401(), OperadorEmergenciasPermission()]
        return [IsAuthenticated401(), AccidentesLecturaPermission()]

    def get(self, request: Request, idaccidente: str) -> Response:
        row = ConsultaAccidenteService().detalle(idaccidente)
        if not row:
            return error_response("not_found", "Accidente no encontrado", "404", status_code=404)
        return success_response(row)

    def patch(self, request: Request, idaccidente: str) -> Response:
        try:
            data = ConsultaAccidenteService().actualizar(
                idaccidente, request.data, idusuario=request.user.idusuario
            )
        except LookupError:
            return error_response("not_found", "Accidente no encontrado", "404", status_code=404)
        except ValueError as exc:
            return error_response("unprocessable_entity", str(exc), "422", status_code=422)
        return success_response(data)
