"""DRF views for onboarding y validación de región operativa (CU-O55/O60/O61/O62)."""

from __future__ import annotations

from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.red_operativa.idempotency import get_cached_response, store_response
from apps.red_operativa.permissions import (
    IsAdministradorOrDirectorTecnologico,
    IsAdministradorRedOperativa,
    IsDirectorTecnologico,
)
from apps.red_operativa.services.despublicacion_automatica_service import (
    DespublicacionAutomaticaService,
)
from apps.red_operativa.services.reevaluacion_region_service import ReevaluacionRegionService
from apps.red_operativa.services.remediacion_region_service import RemediacionRegionService
from apps.red_operativa.services.validacion_region_service import ValidacionRegionService
from core.api.response_envelope import error_response, success_response
from core.repositories.red_operativa.region_operativa_repository import (
    RegionOperativaRepository,
)


def _roles(request: Request) -> list[str]:
    return list(getattr(request.user, "roles", []) or [])


class RegionListView(APIView):
    """GET /red-operativa/regiones."""

    permission_classes = [IsAdministradorOrDirectorTecnologico]

    def get(self, request: Request) -> Response:
        cursor = int(request.query_params.get("cursor") or 0)
        limit = int(request.query_params.get("limit") or 20)
        estadoregion = request.query_params.get("estadoregion") or None
        items = RegionOperativaRepository().list(
            cursor=cursor, limit=limit, estadoregion=estadoregion
        )
        return success_response({"items": items})


class RegionDetalleView(APIView):
    """GET /red-operativa/regiones/{id}."""

    permission_classes = [IsAdministradorOrDirectorTecnologico]

    def get(self, request: Request, idregionoperativa: int) -> Response:
        region = RegionOperativaRepository().find_by_id(idregionoperativa)
        if not region:
            return error_response("not_found", "Región no encontrada", "404", status_code=404)
        return success_response(region)


class RegionValidacionView(APIView):
    """POST /red-operativa/regiones/validaciones (CU-O55)."""

    permission_classes = [IsAdministradorOrDirectorTecnologico]
    parser_classes = [JSONParser]

    def post(self, request: Request) -> Response:
        cached = get_cached_response(request, "region_validacion")
        if cached is not None:
            return cached
        try:
            data = ValidacionRegionService().ejecutar(
                dict(request.data),
                idusuario=request.user.idusuario,
                roles=_roles(request),
            )
        except LookupError:
            return error_response("not_found", "Región no encontrada", "404", status_code=404)
        except PermissionError as exc:
            return error_response("forbidden", str(exc), "403", status_code=403)
        except (KeyError, ValueError) as exc:
            return error_response("bad_request", str(exc), "400", status_code=400)
        response = success_response(data)
        store_response(request, "region_validacion", response)
        return response


class RegionValidacionHistorialView(APIView):
    """GET /red-operativa/regiones/{id}/validaciones (CU-O60)."""

    permission_classes = [IsAdministradorOrDirectorTecnologico]

    def get(self, request: Request, idregionoperativa: int) -> Response:
        if not RegionOperativaRepository().find_by_id(idregionoperativa):
            return error_response("not_found", "Región no encontrada", "404", status_code=404)
        historial = RemediacionRegionService().historial(idregionoperativa)
        return success_response(historial)


class RegionRechazoDefinitivoView(APIView):
    """POST /red-operativa/regiones/{id}/rechazo-definitivo (CU-O60)."""

    permission_classes = [IsAdministradorRedOperativa]
    parser_classes = [JSONParser]

    def post(self, request: Request, idregionoperativa: int) -> Response:
        cached = get_cached_response(request, f"rechazo_definitivo:{idregionoperativa}")
        if cached is not None:
            return cached
        try:
            data = RemediacionRegionService().rechazo_definitivo(idregionoperativa)
        except LookupError:
            return error_response("not_found", "Región no encontrada", "404", status_code=404)
        except ValueError as exc:
            return error_response("conflict", str(exc), "409", status_code=409)
        response = success_response(data)
        store_response(request, f"rechazo_definitivo:{idregionoperativa}", response)
        return response


class RegionDespublicacionAutomaticaView(APIView):
    """POST /red-operativa/regiones/{id}/despublicacion-automatica (CU-O62).

    Invocable manualmente (Administrador) o por job/cron cuando cobertura = 0
    (puente geo → condados → unidades activas).
    """

    permission_classes = [IsAdministradorRedOperativa]

    def post(self, request: Request, idregionoperativa: int) -> Response:
        cached = get_cached_response(request, f"despublicacion:{idregionoperativa}")
        if cached is not None:
            return cached
        try:
            data = DespublicacionAutomaticaService().ejecutar(idregionoperativa)
        except LookupError:
            return error_response("not_found", "Región no encontrada", "404", status_code=404)
        except ValueError as exc:
            return error_response("conflict", str(exc), "409", status_code=409)
        response = success_response(data)
        store_response(request, f"despublicacion:{idregionoperativa}", response)
        return response


class RegionReevaluacionView(APIView):
    """POST /red-operativa/regiones/{id}/reevaluacion (CU-O61)."""

    permission_classes = [IsDirectorTecnologico]
    parser_classes = [JSONParser]

    def post(self, request: Request, idregionoperativa: int) -> Response:
        cached = get_cached_response(request, f"reevaluacion:{idregionoperativa}")
        if cached is not None:
            return cached
        estadoregion = request.data.get("estadoregion")
        motivo = request.data.get("motivo")
        if not estadoregion or not motivo:
            return error_response(
                "bad_request", "estadoregion y motivo son requeridos", "400", status_code=400
            )
        try:
            data = ReevaluacionRegionService().reevaluar(
                idregionoperativa,
                estadoregion_nuevo=estadoregion,
                motivo=motivo,
                idusuario=request.user.idusuario,
            )
        except LookupError:
            return error_response("not_found", "Región no encontrada", "404", status_code=404)
        except KeyError as exc:
            return error_response("bad_request", str(exc), "400", status_code=400)
        except ValueError as exc:
            return error_response("conflict", str(exc), "409", status_code=409)
        response = success_response(data)
        store_response(request, f"reevaluacion:{idregionoperativa}", response)
        return response
