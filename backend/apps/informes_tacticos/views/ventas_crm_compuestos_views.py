"""Vista de los informes compuestos de Ventas y CRM.

Una vista parametrizada, sobre las mismas piezas que los otros dos
departamentos: período con defecto de 30 días, repositorio del modelo y envelope.

⚠️ Es la primera de los compuestos que **acota por titularidad**
-----------------------------------------------------------------
El Director de Marketing ve el departamento entero; el ejecutivo comercial ve
sus propios prospectos. El acotamiento se decide aquí —quién es el solicitante—
y se aplica en la consulta, no filtrando la respuesta después: filtrar después
habría traído del almacén los prospectos de todos para descartarlos en Python,
que además de costoso deja el dato ajeno pasando por la memoria del proceso.

La respuesta **declara el alcance** en `acotado_a`. Una cifra acotada y una
completa se ven idénticas, y sin ese campo un ejecutivo y su director verían la
misma pantalla con números distintos sin saber por qué.
"""

from __future__ import annotations

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.informes_tacticos.envelope import informe_acotado
from apps.informes_tacticos.periodo import PeriodoInvalido, parse_periodo_con_defecto
from apps.informes_tacticos.permissions import (
    ROLE_ADMIN,
    ROLE_GERENTE_VENTAS,
    VentasCrmCompuestosPermission,
)
from apps.informes_tacticos.services.ventas_crm_compuestos_service import (
    InformeDesconocido,
    VentasCrmCompuestosService,
)
from core.api.response_envelope import error_response
from core.auth.permissions import IsAuthenticated401
from core.auth.roles_tacticos import AUTORIDAD_VENTAS_CRM


class VentasCrmCompuestoView(APIView):
    """`GET /informes-tacticos/ventas-crm/<informe>`."""

    permission_classes = [IsAuthenticated401, VentasCrmCompuestosPermission]

    def get(self, request: Request, informe: str) -> Response:
        try:
            periodo = parse_periodo_con_defecto(request.query_params)
        except PeriodoInvalido as exc:
            return error_response("bad_request", str(exc), "400", status_code=400)

        servicio = VentasCrmCompuestosService()
        try:
            datos, alcance = servicio.calcular(
                informe, periodo, idejecutivo=_acotamiento_de(request.user)
            )
        except InformeDesconocido:
            return error_response(
                "not_found",
                f"No existe el informe '{informe}'. "
                f"Publicados: {', '.join(servicio.informes_publicados())}.",
                "404",
                status_code=404,
            )

        return informe_acotado(datos, periodo, acotado_a=alcance)


def _acotamiento_de(usuario) -> int | None:
    """El identificador por el que acotar, o `None` si no hay que acotar.

    ⚠️ Devolver `None` significa **ver todo**, así que el defecto tiene que ser
    lo contrario: si el rol no da vista de departamento, se acota. Un `None` por
    descuido —un rol nuevo que nadie clasificó— abriría el departamento entero a
    quien no le corresponde, y en silencio.

    Por eso la condición se escribe en positivo sobre la autoridad, y no en
    negativo sobre los demás roles.
    """
    roles = set(getattr(usuario, "roles", []))

    if roles & AUTORIDAD_VENTAS_CRM:
        return None

    if roles & {ROLE_ADMIN, ROLE_GERENTE_VENTAS}:
        # `AuthenticatedUser.idusuario` — no `id` ni `pk`: este usuario no es un
        # modelo de Django, es el dataclass que construye la autenticación por
        # JWT. Es lo único que se usa de su identidad, y no viaja a la respuesta.
        try:
            return int(getattr(usuario, "idusuario", 0) or 0)
        except (TypeError, ValueError):
            return 0

    # No debería llegarse aquí —el permiso ya filtró— pero si se llegara, se
    # acota a un identificador imposible en vez de abrir el departamento.
    return 0
