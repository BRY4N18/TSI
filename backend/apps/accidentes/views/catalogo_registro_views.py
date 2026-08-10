"""DRF views for registro catalogos (tipo reportado, estación, unidades)."""

from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accidentes.permissions import (
    AccidentesLecturaPermission,
    IsTecnicoCampoOrUnidadOrAdmin,
)
from apps.accidentes.services.catalogo_registro_service import CatalogoRegistroService
from core.api.response_envelope import success_response
from core.auth.permissions import IsAuthenticated401


class TipoReportadoListView(APIView):
    permission_classes = [IsAuthenticated401, AccidentesLecturaPermission]

    def get(self, request: Request) -> Response:
        return success_response(CatalogoRegistroService().listar_tipos_reportado())


class ReferenciaEstacionListView(APIView):
    permission_classes = [IsAuthenticated401, AccidentesLecturaPermission]

    def get(self, request: Request) -> Response:
        return success_response(CatalogoRegistroService().listar_referencias_estacion())


class UnidadesEmergenciaCatalogoView(APIView):
    """Catálogo de unidades activas para selección (p. ej. CU-O73 unidad adicional)."""

    permission_classes = [IsAuthenticated401, IsTecnicoCampoOrUnidadOrAdmin]

    def get(self, request: Request) -> Response:
        return success_response(CatalogoRegistroService().listar_unidades_emergencia())
