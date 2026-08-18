"""Vista de los informes compuestos de Soporte al Cliente.

El permiso abre la puerta; el acotamiento por agente se decide aquí y se
aplica en la consulta, no filtrando la respuesta después.
"""

from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.informes_tacticos.envelope import informe_soporte
from apps.informes_tacticos.periodo import PeriodoInvalido, parse_periodo, parse_periodo_con_defecto
from apps.informes_tacticos.permissions import (
    ROLE_ADMIN,
    ROLE_AGENTE_SOPORTE,
    SoporteCompuestosPermission,
)
from apps.informes_tacticos.services.soporte_compuestos_service import (
    AGRUPAR_COLA,
    EJES_REINCIDENCIA,
    GRANULARIDAD_DEFECTO,
    GRANULARIDADES,
    InformeDesconocido,
    SoporteCompuestosService,
)
from core.api.response_envelope import error_response
from core.auth.permissions import IsAuthenticated401
from core.auth.roles_tacticos import AUTORIDAD_SOPORTE

RUTA_POR_PLAN = "cumplimiento-sla-por-plan"


class SoporteCompuestoView(APIView):
    """`GET /informes-tacticos/soporte/<informe>`."""

    permission_classes = [IsAuthenticated401, SoporteCompuestosPermission]

    def get(self, request: Request, informe: str) -> Response:
        return _responder(request, informe)


class SoporteCumplimientoPorPlanView(APIView):
    """`GET /informes-tacticos/soporte/cumplimiento-sla/por-plan`."""

    permission_classes = [IsAuthenticated401, SoporteCompuestosPermission]

    def get(self, request: Request) -> Response:
        return _responder(request, RUTA_POR_PLAN)


def _responder(request: Request, informe: str) -> Response:
    try:
        extra, periodo = _leer(informe, request.query_params)
    except PeriodoInvalido as exc:
        return error_response("bad_request", str(exc), "400", status_code=400)
    except ValueError as exc:
        return error_response("bad_request", str(exc), "400", status_code=400)

    servicio = SoporteCompuestosService()
    try:
        cuerpo, alcance = servicio.calcular(
            informe,
            periodo,
            idagente=_acotamiento_de(request.user),
            extra=extra,
        )
    except InformeDesconocido:
        return error_response(
            "not_found",
            f"No existe el informe '{informe}'. "
            f"Publicados: {', '.join(servicio.informes_publicados())}.",
            "404",
            status_code=404,
        )

    return informe_soporte(cuerpo, periodo, acotado_a=alcance, filtros=dict(extra))


def _params_planos(query_params) -> dict:
    """QueryDict guarda listas; parse_periodo espera cadenas."""
    return {clave: query_params.get(clave) for clave in query_params}


def _leer(informe: str, query_params) -> tuple[dict, object]:
    extra: dict = {}
    granularidad = query_params.get("granularidad") or GRANULARIDAD_DEFECTO
    if granularidad not in GRANULARIDADES:
        raise ValueError(
            f"granularidad '{granularidad}' no soportada, use una de: {sorted(GRANULARIDADES)}."
        )
    extra["granularidad"] = granularidad

    if informe == "tablero-cola":
        agrupar = query_params.get("agrupar_por") or "estado"
        if agrupar not in AGRUPAR_COLA:
            raise ValueError(
                f"agrupar_por '{agrupar}' no soportado, use una de: {sorted(AGRUPAR_COLA)}."
            )
        extra["agrupar_por"] = agrupar
        if query_params.get("desde") or query_params.get("hasta"):
            extra["periodo_pedido"] = True
            params = _params_planos(query_params)
            params.setdefault("granularidad", GRANULARIDAD_DEFECTO)
            return extra, parse_periodo(params)
        extra["periodo_pedido"] = False
        return extra, None

    extra["periodo_pedido"] = True
    params = _params_planos(query_params)
    params.setdefault("granularidad", GRANULARIDAD_DEFECTO)
    if not params.get("desde") and not params.get("hasta"):
        periodo = parse_periodo_con_defecto(params)
    else:
        periodo = parse_periodo(params)

    if informe == "reincidencia-clientes":
        eje = query_params.get("eje", "tipo_incidencia")
        if eje not in EJES_REINCIDENCIA:
            raise ValueError(f"eje '{eje}' no soportado, use una de: {sorted(EJES_REINCIDENCIA)}.")
        extra["eje"] = eje
        minimo = query_params.get("minimo", 2)
        try:
            extra["minimo"] = int(minimo)
        except (TypeError, ValueError) as exc:
            raise ValueError("'minimo' debe ser un numero entero.") from exc
        if extra["minimo"] < 2:
            raise ValueError("'minimo' debe ser al menos 2.")

    return extra, periodo


def _acotamiento_de(usuario) -> int | None:
    """`None` = ver todo. Cualquier otro rol se acota a su identificador."""
    roles = set(getattr(usuario, "roles", []))
    if roles & AUTORIDAD_SOPORTE:
        return None
    if roles & {ROLE_ADMIN, ROLE_AGENTE_SOPORTE}:
        try:
            return int(getattr(usuario, "idusuario", 0) or 0)
        except (TypeError, ValueError):
            return 0
    return 0
