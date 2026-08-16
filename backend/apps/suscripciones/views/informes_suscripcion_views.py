"""Vista de suscripciones — L1 de OT05/OT07.

Listado de **estado actual**: rechaza el período genérico (`desde`/`hasta`) con
`400`. Lo que sí acepta es `cancelada_desde`/`cancelada_hasta`, que **no son el
período del contrato** sino un filtro sobre la columna de fecha de cancelación:
esta tabla guarda el estado actual de cada suscripción, no un histórico de
sucesos, así que un rango genérico no tendría sobre qué aplicarse.
"""

from __future__ import annotations

from rest_framework.request import Request

from apps.suscripciones.permissions import (
    AMPLIOS_CATALOGO,
    ROLES_INFORMES_ACOTADOS,
    InformesCatalogoPermission,
)
from apps.suscripciones.services.informes_suscripcion_service import (
    InformesSuscripcionService,
)
from apps.suscripciones.views.informes_base import ListadoSuscripcionesBaseView
from core.auth.permissions import IsAuthenticated401
from core.informes.acotamiento import AccesoDenegado
from core.informes.envelope import listado_response
from core.informes.paginacion import parse_dir
from core.informes.periodo import parse_fecha_columna
from core.informes.vistas import ERRORES_DE_VALIDACION
from core.repositories.suscripciones.informes_suscripcion_repository import (
    CURSOR_SUSCRIPCIONES,
    ESTADOS_SUSCRIPCION,
    ORDEN_SUSCRIPCIONES,
)

DIA_MS = 86_400_000


class SuscripcionesView(ListadoSuscripcionesBaseView):
    permission_classes = [IsAuthenticated401, InformesCatalogoPermission]
    admite_rango = False
    roles_amplios = AMPLIOS_CATALOGO
    roles_acotados = ROLES_INFORMES_ACOTADOS

    def get(self, request: Request):
        try:
            _, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_SUSCRIPCIONES)
            cursor = CURSOR_SUSCRIPCIONES.decodificar(request.query_params.get("cursor"))
            estado = self.parse_enumeracion(
                request.query_params, "estado", ESTADOS_SUSCRIPCION
            )
            idplan = self.parse_entero(request.query_params, "plan", minimo=1)
            vence_en_dias = self.parse_entero(
                request.query_params, "vence_en_dias", minimo=0
            )
            con_cambio = self.parse_booleano(
                request.query_params, "con_cambio_programado"
            )
            cancelada_desde = parse_fecha_columna(
                request.query_params, "cancelada_desde"
            )
            cancelada_hasta = parse_fecha_columna(
                request.query_params, "cancelada_hasta", inclusivo_al_final=True
            )
            acotamiento = self.acotar(request)
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)
        except AccesoDenegado as exc:
            return self.manejar_acceso_denegado(exc)

        pagina = InformesSuscripcionService().suscripciones(
            acotamiento=acotamiento,
            cursor=cursor,
            limit=limit,
            orden=orden,
            estado=estado,
            idplan=idplan,
            con_cambio_programado=con_cambio,
            vence_en_dias=vence_en_dias,
            cancelada_desde_ms=cancelada_desde,
            cancelada_hasta_ms=cancelada_hasta,
        )
        return listado_response(
            pagina,
            {
                "estado": estado,
                "plan": idplan,
                "vence_en_dias": vence_en_dias,
                "con_cambio_programado": con_cambio,
                "cancelada_desde": request.query_params.get("cancelada_desde") or None,
                "cancelada_hasta": request.query_params.get("cancelada_hasta") or None,
                "cuenta": acotamiento.titular,
            },
            acotado_a=acotamiento.alcance,
        )

