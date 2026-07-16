"""Proxy de ruteo por calles (OSRM) para el mapa de seguimiento."""

from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.response_envelope import error_response, success_response
from apps.cuentas_clientes.permissions import IsAuthenticated401
from apps.seguimiento.permissions import IsOperadorSeguimiento
from apps.seguimiento.services.ruta_service import RutaCoordenadasInvalidasError, RutaService


class RutaSeguimientoView(APIView):
    permission_classes = [IsAuthenticated401, IsOperadorSeguimiento]

    def get(self, request: Request) -> Response:
        origen_raw = request.query_params.get("origen")
        destino_raw = request.query_params.get("destino")
        if not origen_raw or not destino_raw:
            return error_response(
                "bad_request", "Parámetros 'origen' y 'destino' son requeridos", "400", status_code=400
            )

        try:
            data = RutaService().obtener_ruta(origen_raw, destino_raw)
        except RutaCoordenadasInvalidasError as exc:
            return error_response("bad_request", str(exc), "400", status_code=400)

        return success_response(data)
