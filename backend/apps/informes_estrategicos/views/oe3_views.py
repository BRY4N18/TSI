"""Vista parametrizada de los siete informes publicados de OE3.

El nombre llega por la URL y se busca en el registro. Un bloqueado no está
en `PUBLICADOS` y responde 404, no 200 vacío.
"""

from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

import requests

from apps.informes_estrategicos.envelope import informe_estrategico_response
from apps.informes_estrategicos.periodo_estrategico import (
    PeriodoEstrategicoInvalido,
    parse_comparacion,
    parse_periodo_estrategico,
)
from apps.informes_estrategicos.permissions import Oe3Permission
from apps.informes_estrategicos.services.oe3_service import Oe3Service
from apps.informes_estrategicos.services.oe6_service import InformeDesconocido
from core.api.response_envelope import error_response
from core.auth.permissions import IsAuthenticated401

SIN_GRANULARIDAD = frozenset({"cobertura-de-respaldo"})


class Oe3View(APIView):
    """`GET /informes-estrategicos/oe3/<informe>`."""

    permission_classes = [IsAuthenticated401, Oe3Permission]

    def get(self, request: Request, informe: str) -> Response:
        params = request.query_params
        if informe in SIN_GRANULARIDAD and not params.get("granularidad"):
            params = params.copy()
            params["granularidad"] = "mes"
        try:
            periodo = parse_periodo_estrategico(params)
            comparacion = parse_comparacion(params)
        except PeriodoEstrategicoInvalido as exc:
            return error_response("bad_request", str(exc), "400", status_code=400)

        servicio = Oe3Service()
        try:
            extra = {
                parametro.nombre: parametro.leer(params.get(parametro.nombre))
                for parametro in servicio.parametros_de(informe)
            }
        except ValueError as exc:
            return error_response("bad_request", str(exc), "400", status_code=400)

        try:
            resultado = servicio.calcular(
                informe, periodo, comparacion=comparacion, extra=extra
            )
        except InformeDesconocido:
            return error_response(
                "not_found",
                f"No existe el informe '{informe}'. "
                f"Publicados: {', '.join(servicio.informes_publicados())}.",
                "404",
                status_code=404,
            )
        except requests.RequestException:
            return error_response(
                "service_unavailable",
                "El almacén analítico no está disponible.",
                "503",
                status_code=503,
            )

        return informe_estrategico_response(
            resultado.data,
            periodo,
            comparacion=resultado.comparacion,
            objetivo=resultado.objetivo,
            cobertura=resultado.cobertura,
            falta=resultado.falta,
            alcance=resultado.alcance,
        )
