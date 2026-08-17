"""Vista parametrizada de los doce informes de OE6.

Una sola clase: lo único que cambiaría entre doce es una cadena. El nombre llega
por la URL y se busca en el registro; si no está, es un 404. No se convierte en
ruta de fichero.
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
from apps.informes_estrategicos.permissions import Oe6Permission
from apps.informes_estrategicos.services.oe6_service import (
    InformeDesconocido,
    Oe6Service,
)
from core.api.response_envelope import error_response
from core.auth.permissions import IsAuthenticated401


class Oe6View(APIView):
    """`GET /informes-estrategicos/oe6/<informe>`."""

    permission_classes = [IsAuthenticated401, Oe6Permission]

    def get(self, request: Request, informe: str) -> Response:
        try:
            periodo = parse_periodo_estrategico(request.query_params)
            comparacion = parse_comparacion(request.query_params)
        except PeriodoEstrategicoInvalido as exc:
            return error_response("bad_request", str(exc), "400", status_code=400)

        servicio = Oe6Service()
        try:
            extra = {
                parametro.nombre: parametro.leer(request.query_params.get(parametro.nombre))
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
