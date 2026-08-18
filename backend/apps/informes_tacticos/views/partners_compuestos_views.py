"""Vista de los informes compuestos de Partners y API."""

from __future__ import annotations

from typing import Any

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.informes_tacticos.envelope import informe_partners
from apps.informes_tacticos.periodo import PeriodoInvalido, parse_periodo_con_defecto
from apps.informes_tacticos.permissions import PartnersCompuestosPermission
from apps.informes_tacticos.services.partners_compuestos_service import (
    InformeDesconocido,
    PartnersCompuestosService,
)
from core.api.response_envelope import error_response
from core.auth.permissions import IsAuthenticated401


class PartnersCompuestoView(APIView):
    """`GET /informes-tacticos/partners/<informe>`."""

    permission_classes = [IsAuthenticated401, PartnersCompuestosPermission]

    def get(self, request: Request, informe: str) -> Response:
        try:
            periodo = parse_periodo_con_defecto(request.query_params)
            extra = _leer_parametros(request.query_params)
        except (PeriodoInvalido, ValueError) as exc:
            return error_response("bad_request", str(exc), "400", status_code=400)

        servicio = PartnersCompuestosService()
        try:
            cuerpo, notas = servicio.calcular(informe, periodo, extra=extra)
        except InformeDesconocido:
            return error_response(
                "not_found",
                f"No existe el informe '{informe}'. "
                f"Publicados: {', '.join(servicio.informes_publicados())}.",
                "404",
                status_code=404,
            )
        return informe_partners(cuerpo, periodo, notas=notas, filtros=dict(extra))


def _entero(nombre: str, valor: Any, minimo: int = 1) -> int:
    try:
        n = int(valor)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"'{nombre}' debe ser un numero entero.") from exc
    if n < minimo:
        raise ValueError(f"'{nombre}' debe ser mayor o igual que {minimo}.")
    return n


def _leer_parametros(query_params) -> dict[str, Any]:
    extra: dict[str, Any] = {}
    if query_params.get("percentil") is not None:
        extra["percentil"] = _entero("percentil", query_params.get("percentil"), minimo=1)
    if query_params.get("muestra_minima") is not None:
        extra["muestra_minima"] = _entero(
            "muestra_minima", query_params.get("muestra_minima"), minimo=1
        )
    mes = query_params.get("mes")
    if mes:
        extra["mes"] = str(mes)
    if query_params.get("dias_aviso_expiracion") is not None:
        extra["dias_aviso_expiracion"] = _entero(
            "dias_aviso_expiracion", query_params.get("dias_aviso_expiracion"), minimo=0
        )
    return extra
