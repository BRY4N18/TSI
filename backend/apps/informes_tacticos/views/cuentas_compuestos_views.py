"""Vista de los informes compuestos de Cuentas y Clientes."""

from __future__ import annotations

from typing import Any

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.informes_tacticos.envelope import informe_cuentas
from apps.informes_tacticos.periodo import PeriodoInvalido, parse_periodo_con_defecto
from apps.informes_tacticos.permissions import CuentasCompuestosPermission
from apps.informes_tacticos.services.cuentas_compuestos_service import (
    CuentasCompuestosService,
    InformeDesconocido,
)
from core.api.response_envelope import error_response
from core.auth.permissions import IsAuthenticated401


class CuentasCompuestoView(APIView):
    """`GET /informes-tacticos/cuentas/<informe>`."""

    permission_classes = [IsAuthenticated401, CuentasCompuestosPermission]

    def get(self, request: Request, informe: str) -> Response:
        try:
            periodo = parse_periodo_con_defecto(request.query_params)
            extra = _leer_parametros(request.query_params)
        except (PeriodoInvalido, ValueError) as exc:
            return error_response("bad_request", str(exc), "400", status_code=400)

        servicio = CuentasCompuestosService()
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
        return informe_cuentas(cuerpo, periodo, notas=notas, filtros=dict(extra))


def _leer_parametros(query_params) -> dict[str, Any]:
    extra: dict[str, Any] = {}
    mes = query_params.get("mes_cohorte")
    if mes:
        extra["mes_cohorte"] = str(mes)
    dias = query_params.get("dias_inactividad")
    if dias is not None:
        try:
            valor = int(dias)
        except (TypeError, ValueError) as exc:
            raise ValueError("'dias_inactividad' debe ser un numero entero.") from exc
        if valor < 1:
            raise ValueError("'dias_inactividad' debe ser mayor que cero.")
        extra["dias_inactividad"] = valor
    pares = query_params.get("pares_incompatibles")
    if pares is not None:
        extra["pares_incompatibles"] = str(pares)
    return extra
