"""Vista de los informes compuestos de Suscripciones y Facturación.

El permiso depende del **informe pedido**: la autoridad está repartida, y un
permiso no puede depender de un parámetro de consulta que se lee después de
concederlo.
"""

from __future__ import annotations

from typing import Any

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.informes_tacticos.envelope import informe_con_periodo_natural
from apps.informes_tacticos.periodo import PeriodoInvalido, parse_periodo_con_defecto
from apps.informes_tacticos.permissions import SuscripcionesCompuestosPermission
from apps.informes_tacticos.services.suscripciones_compuestos_service import (
    INFORMES_MES_NATURAL,
    PARAMETROS,
    InformeDesconocido,
    SuscripcionesCompuestosService,
    mes_natural_de,
)
from core.api.response_envelope import error_response
from core.auth.permissions import IsAuthenticated401


class SuscripcionesCompuestoView(APIView):
    """`GET /informes-tacticos/suscripciones/<informe>`."""

    permission_classes = [IsAuthenticated401, SuscripcionesCompuestosPermission]

    def get(self, request: Request, informe: str) -> Response:
        try:
            periodo = parse_periodo_con_defecto(request.query_params)
        except PeriodoInvalido as exc:
            return error_response("bad_request", str(exc), "400", status_code=400)

        servicio = SuscripcionesCompuestosService()
        try:
            extra = _leer_parametros(informe, request.query_params)
        except ValueError as exc:
            return error_response("bad_request", str(exc), "400", status_code=400)

        mes = None
        nota_periodo = None
        if informe in INFORMES_MES_NATURAL:
            mes, nota_periodo = mes_natural_de(periodo, request.query_params.get("mes"))
            extra["mes"] = mes

        try:
            datos = servicio.calcular(informe, periodo, extra=extra)
        except InformeDesconocido:
            return error_response(
                "not_found",
                f"No existe el informe '{informe}'. "
                f"Publicados: {', '.join(servicio.informes_publicados())}.",
                "404",
                status_code=404,
            )

        return informe_con_periodo_natural(
            datos,
            periodo,
            mes=mes,
            nota_periodo=nota_periodo,
            filtros=dict(extra),
        )


def _leer_parametros(informe: str, query_params) -> dict[str, Any]:
    valores: dict[str, Any] = {}
    for nombre, defecto in PARAMETROS.get(informe, {}).items():
        crudo = query_params.get(nombre)
        if crudo is None:
            valores[nombre] = defecto
            continue
        if isinstance(defecto, int):
            try:
                valor = int(crudo)
            except (TypeError, ValueError):
                raise ValueError(f"'{nombre}' debe ser un numero entero.") from None
            if valor < 1:
                raise ValueError(f"'{nombre}' debe ser mayor que cero.")
            valores[nombre] = valor
        else:
            valores[nombre] = str(crudo)
    return valores
