"""Vista de solicitudes de cambio de plan — L3 de OT07 / CU-O34.

Listado de **estado actual** —una solicitud *está* pendiente o resuelta— y va con
el permiso de **catálogo**: es el Director de Estrategia quien decide precios y
planes, así que los movimientos de plan son su materia (§5.1 del SRS).
"""

from __future__ import annotations

from rest_framework.request import Request

from apps.suscripciones.permissions import (
    AMPLIOS_CATALOGO,
    ROLES_INFORMES_ACOTADOS,
    InformesCatalogoPermission,
)
from apps.suscripciones.services.informes_cambio_plan_service import (
    InformesCambioPlanService,
)
from apps.suscripciones.views.informes_base import ListadoSuscripcionesBaseView
from core.auth.permissions import IsAuthenticated401
from core.informes.acotamiento import AccesoDenegado
from core.informes.envelope import listado_response
from core.informes.paginacion import parse_dir
from core.informes.vistas import ERRORES_DE_VALIDACION
from core.repositories.suscripciones.informes_cambio_plan_repository import (
    CURSOR_SOLICITUDES,
    ESTADOS_SOLICITUD,
    ORDEN_SOLICITUDES,
)


class SolicitudesCambioPlanView(ListadoSuscripcionesBaseView):
    permission_classes = [IsAuthenticated401, InformesCatalogoPermission]
    admite_rango = False
    roles_amplios = AMPLIOS_CATALOGO
    roles_acotados = ROLES_INFORMES_ACOTADOS

    def get(self, request: Request):
        try:
            _, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_SOLICITUDES)
            cursor = CURSOR_SOLICITUDES.decodificar(request.query_params.get("cursor"))
            estado = self.parse_enumeracion(
                request.query_params, "estado", ESTADOS_SOLICITUD
            )
            acotamiento = self.acotar(request)
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)
        except AccesoDenegado as exc:
            return self.manejar_acceso_denegado(exc)

        pagina = InformesCambioPlanService().solicitudes(
            acotamiento=acotamiento, cursor=cursor, limit=limit, orden=orden, estado=estado
        )
        return listado_response(
            pagina,
            {"estado": estado, "cuenta": acotamiento.titular},
            acotado_a=acotamiento.alcance,
        )
