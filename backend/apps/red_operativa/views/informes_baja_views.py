"""Vista de bajas de unidad — L2 de OT12 / CU-O42.

Listado de **hechos del período**: una baja ocurre en un instante. Acotado por
proveedor, con el mismo criterio estricto que la flota.
"""

from __future__ import annotations

from rest_framework.request import Request

from apps.red_operativa.permissions import (
    AMPLIOS_FLOTA,
    ROLES_INFORMES_FLOTA_ACOTADOS,
    InformesFlotaPermission,
)
from apps.red_operativa.services.informes_baja_service import InformesBajaService
from apps.red_operativa.views.informes_base import ListadoRedOperativaBaseView
from core.auth.permissions import IsAuthenticated401
from core.informes.acotamiento import AccesoDenegado
from core.informes.envelope import listado_response
from core.informes.paginacion import parse_dir
from core.informes.vistas import ERRORES_DE_VALIDACION
from core.repositories.red_operativa.informes_baja_repository import (
    CURSOR_BAJAS,
    ORDEN_BAJAS,
    TIPOS_BAJA,
)


class BajasUnidadView(ListadoRedOperativaBaseView):
    permission_classes = [IsAuthenticated401, InformesFlotaPermission]
    admite_rango = True
    roles_amplios = AMPLIOS_FLOTA
    roles_acotados = ROLES_INFORMES_FLOTA_ACOTADOS

    def get(self, request: Request):
        try:
            periodo, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_BAJAS)
            cursor = CURSOR_BAJAS.decodificar(request.query_params.get("cursor"))
            # Los dos tipos son un catálogo cerrado y con significado muy
            # distinto: la enumeración se valida y el error los nombra.
            tipo_baja = self.parse_enumeracion(
                request.query_params, "tipo_baja", TIPOS_BAJA
            )
            acotamiento = self.acotar(request)
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)
        except AccesoDenegado as exc:
            return self.manejar_acceso_denegado(exc)

        pagina = InformesBajaService().bajas(
            acotamiento=acotamiento,
            cursor=cursor,
            limit=limit,
            orden=orden,
            desde_ms=periodo.desde_ms,
            hasta_ms=periodo.hasta_ms,
            tipo_baja=tipo_baja,
        )
        return listado_response(
            pagina,
            {
                **periodo.to_meta(),
                "tipo_baja": tipo_baja,
                "proveedor": acotamiento.titular,
            },
            acotado_a=acotamiento.alcance,
        )
