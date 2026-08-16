"""Vistas de facturación — L2 facturas y L4 métodos de pago vigentes.

Los dos van con el permiso de **finanzas**: aquí la autoridad departamental es el
Director Financiero, que responde por el resultado económico. El de Estrategia,
que decide catálogo y precios, **no** accede a estos dos (§5.1 del SRS).

`facturas` es de hechos del período —una factura se emite en un instante— y
`metodos-pago` de estado actual: un medio de cobro *está* vigente o no.
"""

from __future__ import annotations

from rest_framework.request import Request

from apps.suscripciones.permissions import (
    AMPLIOS_FINANZAS,
    ROLES_INFORMES_ACOTADOS,
    InformesFinanzasPermission,
)
from apps.suscripciones.services.informes_facturacion_service import (
    InformesFacturacionService,
)
from apps.suscripciones.views.informes_base import ListadoSuscripcionesBaseView
from core.auth.permissions import IsAuthenticated401
from core.informes.acotamiento import AccesoDenegado
from core.informes.envelope import listado_response
from core.informes.paginacion import parse_dir
from core.informes.vistas import ERRORES_DE_VALIDACION
from core.repositories.suscripciones.informes_facturacion_repository import (
    CURSOR_FACTURAS,
    CURSOR_METODOS,
    ESTADOS_PAGO,
    ORDEN_FACTURAS,
    ORDEN_METODOS,
)


class _ListadoFinanzasView(ListadoSuscripcionesBaseView):
    permission_classes = [IsAuthenticated401, InformesFinanzasPermission]
    roles_amplios = AMPLIOS_FINANZAS
    roles_acotados = ROLES_INFORMES_ACOTADOS


class FacturasView(_ListadoFinanzasView):
    """L2 — facturas con su estado y su mora."""

    admite_rango = True

    def get(self, request: Request):
        try:
            periodo, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_FACTURAS)
            cursor = CURSOR_FACTURAS.decodificar(request.query_params.get("cursor"))
            estado_pago = self.parse_enumeracion(
                request.query_params, "estado_pago", ESTADOS_PAGO
            )
            # `vencidas` excluye las que están en disputa: el sistema dejó de
            # cobrarlas a propósito y perseguirlas es el defecto que corrigió B41.
            vencidas = self.parse_booleano(request.query_params, "vencidas") or False
            acotamiento = self.acotar(request)
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)
        except AccesoDenegado as exc:
            return self.manejar_acceso_denegado(exc)

        pagina = InformesFacturacionService().facturas(
            acotamiento=acotamiento,
            cursor=cursor,
            limit=limit,
            orden=orden,
            estado_pago=estado_pago,
            desde_ms=periodo.desde_ms,
            hasta_ms=periodo.hasta_ms,
            solo_vencidas=vencidas,
        )
        return listado_response(
            pagina,
            {
                **periodo.to_meta(),
                "estado_pago": estado_pago,
                "vencidas": vencidas or None,
                "cuenta": acotamiento.titular,
            },
            acotado_a=acotamiento.alcance,
        )


class MetodosPagoView(_ListadoFinanzasView):
    """L4 — medios de cobro vigentes. ⛔ El identificador de cobro no sale."""

    admite_rango = False

    def get(self, request: Request):
        try:
            _, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_METODOS)
            cursor = CURSOR_METODOS.decodificar(request.query_params.get("cursor"))
            caduca_en_dias = self.parse_entero(
                request.query_params, "caduca_en_dias", minimo=0
            )
            acotamiento = self.acotar(request)
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)
        except AccesoDenegado as exc:
            return self.manejar_acceso_denegado(exc)

        pagina = InformesFacturacionService().metodos_de_pago(
            acotamiento=acotamiento,
            cursor=cursor,
            limit=limit,
            orden=orden,
            caduca_en_dias=caduca_en_dias,
        )
        return listado_response(
            pagina,
            {"caduca_en_dias": caduca_en_dias, "cuenta": acotamiento.titular},
            acotado_a=acotamiento.alcance,
        )
