"""Vista parametrizada de los nueve informes publicados de OE5."""

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
from apps.informes_estrategicos.permissions import Oe5Permission
from apps.informes_estrategicos.services.oe5_service import REFERENCIAS_OE1, Oe5Service
from apps.informes_estrategicos.services.oe6_service import InformeDesconocido
from core.api.response_envelope import error_response
from core.auth.permissions import IsAuthenticated401


class Oe5View(APIView):
    """`GET /informes-estrategicos/oe5/<informe>`."""

    permission_classes = [IsAuthenticated401, Oe5Permission]

    def get(self, request: Request, informe: str) -> Response:
        params = request.query_params
        try:
            periodo = parse_periodo_estrategico(params)
            comparacion = parse_comparacion(params)
        except PeriodoEstrategicoInvalido as exc:
            return error_response("bad_request", str(exc), "400", status_code=400)

        servicio = Oe5Service()
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
            if informe in REFERENCIAS_OE1:
                detalle = (
                    f"No existe el informe '{informe}' en OE5. "
                    f"Vive en /informes-estrategicos/oe1/{informe}."
                )
            else:
                detalle = (
                    f"No existe el informe '{informe}'. "
                    f"Publicados: {', '.join(servicio.informes_publicados())}."
                )
            return error_response(
                "not_found",
                detalle,
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
