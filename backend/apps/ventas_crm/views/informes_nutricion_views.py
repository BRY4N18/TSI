"""Vistas de la nutrición del prospecto — L3 demos activas y L4 notificaciones.

Los dos son bandejas: su valor es **actuar antes de que la oportunidad se
enfríe**, no revisar a fin de mes.

`demos-activas` es de estado actual —una demo está vigente *ahora*— y
`notificaciones-enviadas` es de hechos del período, con rango opcional.

⚠️ Una página de `demos-activas` puede traer menos filas que el `limit`
-----------------------------------------------------------------------
Es consecuencia declarada del filtro en dos pasos (research D3): el prefiltro por
día trae de más, y el servicio descarta con precisión de segundo las que
expiraron hoy más temprano. **`has_next` sigue siendo la autoridad**; el número
de filas devueltas no lo es. Un consumidor que decida «si vienen menos de
`limit`, se acabó» se dejará demos sin ver.
"""

from __future__ import annotations

from rest_framework.request import Request

from apps.ventas_crm.permissions import (
    ROLES_INFORMES_ACOTADOS,
    ROLES_INFORMES_AMPLIOS,
    InformesVentasLecturaPermission,
)
from apps.ventas_crm.services.informes_nutricion_service import (
    InformesNutricionService,
)
from core.auth.permissions import IsAuthenticated401
from core.informes.acotamiento import AccesoDenegado
from core.informes.envelope import listado_response
from core.informes.paginacion import parse_dir
from core.informes.vistas import ERRORES_DE_VALIDACION, ListadoBaseView
from core.repositories.ventas_crm.informes_nutricion_repository import (
    CURSOR_DEMOS,
    CURSOR_NOTIFICACIONES,
    ORDEN_DEMOS,
    ORDEN_NOTIFICACIONES,
)


class _ListadoNutricionView(ListadoBaseView):
    permission_classes = [IsAuthenticated401, InformesVentasLecturaPermission]

    def acotar(self, request: Request):
        return self.resolver_acotamiento(
            request,
            roles_amplios=ROLES_INFORMES_AMPLIOS,
            roles_acotados=ROLES_INFORMES_ACOTADOS,
            parametro="ejecutivo",
        )


class DemosActivasView(_ListadoNutricionView):
    """L3 — demos vigentes con los días que les quedan."""

    admite_rango = False

    def get(self, request: Request):
        try:
            _, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_DEMOS)
            cursor = CURSOR_DEMOS.decodificar(request.query_params.get("cursor"))
            acotamiento = self.acotar(request)
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)
        except AccesoDenegado as exc:
            return self.manejar_acceso_denegado(exc)

        pagina = InformesNutricionService().demos_activas(
            acotamiento=acotamiento, cursor=cursor, limit=limit, orden=orden
        )
        return listado_response(
            pagina,
            {"ejecutivo": acotamiento.titular},
            acotado_a=acotamiento.alcance,
        )


class NotificacionesEnviadasView(_ListadoNutricionView):
    """L4 — alertas de señal de interés, acotadas por **destinatario**.

    El eje no es el ejecutivo asignado al prospecto sino el del aviso: el gerente
    ve aquellas de las que fue destinatario. Confundirlos le mostraría alertas
    dirigidas a otra persona.
    """

    admite_rango = True

    def get(self, request: Request):
        try:
            periodo, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_NOTIFICACIONES)
            cursor = CURSOR_NOTIFICACIONES.decodificar(request.query_params.get("cursor"))
            # `regla` y `canal` son texto libre: sus valores los escribe el
            # motor de reglas y no viven en ninguna tabla de catálogo.
            regla = request.query_params.get("regla") or None
            canal = request.query_params.get("canal") or None
            acotamiento = self.acotar(request)
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)
        except AccesoDenegado as exc:
            return self.manejar_acceso_denegado(exc)

        pagina = InformesNutricionService().notificaciones_enviadas(
            acotamiento=acotamiento,
            cursor=cursor,
            limit=limit,
            orden=orden,
            desde_ms=periodo.desde_ms,
            hasta_ms=periodo.hasta_ms,
            regla=regla,
            canal=canal,
        )
        return listado_response(
            pagina,
            {
                **periodo.to_meta(),
                "regla": regla,
                "canal": canal,
                "ejecutivo": acotamiento.titular,
            },
            acotado_a=acotamiento.alcance,
        )
