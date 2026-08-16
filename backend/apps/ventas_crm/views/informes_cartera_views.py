"""Vista de la cartera de prospectos — L1 de OT01/OT02.

Es un listado de **estado actual**: describe qué hay en la cartera *ahora*, así
que rechaza `desde`/`hasta` con `400`.

El filtro `estado` acepta tres valores y no dos
-----------------------------------------------
`activo`, `perdido` y `convertido`. Reducirlo a activo/inactivo perdería justo
la distinción que importa, porque los convertidos —los éxitos— también tienen
`activo = false` (research D1). Un valor fuera de los tres responde `400`
nombrándolos.
"""

from __future__ import annotations

from rest_framework.request import Request

from apps.ventas_crm.permissions import (
    ROLES_INFORMES_ACOTADOS,
    ROLES_INFORMES_AMPLIOS,
    InformesVentasLecturaPermission,
)
from apps.ventas_crm.services.informes_cartera_service import InformesCarteraService
from core.auth.permissions import IsAuthenticated401
from core.informes.acotamiento import AccesoDenegado
from core.informes.envelope import listado_response
from core.informes.paginacion import parse_dir
from core.informes.vistas import ERRORES_DE_VALIDACION, ListadoBaseView
from core.repositories.ventas_crm.informes_cartera_repository import (
    CURSOR_CARTERA,
    ESTADOS_VALIDOS,
    ORDEN_CARTERA,
)


class ProspectosView(ListadoBaseView):
    """L1 — cartera de prospectos, acotada al ejecutivo cuando procede."""

    permission_classes = [IsAuthenticated401, InformesVentasLecturaPermission]
    admite_rango = False

    def get(self, request: Request):
        try:
            _, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_CARTERA)
            cursor = CURSOR_CARTERA.decodificar(request.query_params.get("cursor"))
            estado = self.parse_enumeracion(
                request.query_params, "estado", ESTADOS_VALIDOS
            )
            # `canal`, `tipo_organizacion` y `etapa` son texto libre: sus valores
            # son datos de negocio y no viven en ninguna tabla de catálogo, así
            # que una lista cerrada aquí rechazaría con `400` un filtro correcto
            # en cuanto alguien añadiera un canal nuevo.
            canal = request.query_params.get("canal") or None
            tipo_organizacion = request.query_params.get("tipo_organizacion") or None
            etapa = request.query_params.get("etapa") or None

            acotamiento = self.resolver_acotamiento(
                request,
                roles_amplios=ROLES_INFORMES_AMPLIOS,
                roles_acotados=ROLES_INFORMES_ACOTADOS,
                parametro="ejecutivo",
            )
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)
        except AccesoDenegado as exc:
            return self.manejar_acceso_denegado(exc)

        pagina = InformesCarteraService().prospectos(
            acotamiento=acotamiento,
            cursor=cursor,
            limit=limit,
            orden=orden,
            canal=canal,
            tipo_organizacion=tipo_organizacion,
            etapa=etapa,
            estado=estado,
        )
        return listado_response(
            pagina,
            {
                "canal": canal,
                "tipo_organizacion": tipo_organizacion,
                "etapa": etapa,
                "estado": estado,
                "ejecutivo": acotamiento.titular,
            },
            acotado_a=acotamiento.alcance,
        )
