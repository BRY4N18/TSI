"""Vistas de regiones e intentos de validación — L3 y L4 de OT11/OT13.

**Sin acotamiento**: una región no pertenece a ninguna empresa de flota, y su
estado es materia de gobierno de la red. Un proveedor recibe `403` en los dos
(FR-012).

Y los dos no van al mismo público. El §5.1 del SRS reparte la autoridad de este
departamento: el Tecnológico fija los criterios de validación, el de Expansión
decide dónde crecer. Ambos necesitan **el estado** de las regiones; solo el
Tecnológico necesita **el detalle de por qué se rechazan**.
"""

from __future__ import annotations

from rest_framework.request import Request

from apps.red_operativa.permissions import (
    AMPLIOS_REGION,
    AMPLIOS_VALIDACION,
    InformesRegionPermission,
    InformesValidacionPermission,
)
from apps.red_operativa.services.informes_region_service import InformesRegionService
from core.auth.permissions import IsAuthenticated401
from core.informes.acotamiento import ACOTADO_TODOS
from core.informes.envelope import listado_response
from core.informes.paginacion import parse_dir
from core.informes.vistas import ERRORES_DE_VALIDACION, FiltroInvalido, ListadoBaseView
from core.repositories.red_operativa.informes_region_repository import (
    CURSOR_REGIONES,
    CURSOR_VALIDACIONES,
    ESTADOS_REGION,
    ORDEN_REGIONES,
    ORDEN_VALIDACIONES,
)


class RegionesView(ListadoBaseView):
    """L3 — estado de cada región. Los cinco estados, sin agrupar."""

    permission_classes = [IsAuthenticated401, InformesRegionPermission]
    admite_rango = False

    def get(self, request: Request):
        try:
            _, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_REGIONES)
            cursor = CURSOR_REGIONES.decodificar(request.query_params.get("cursor"))
            estado = self.parse_enumeracion(
                request.query_params, "estado_region", ESTADOS_REGION
            )
            detenida = self.parse_entero(
                request.query_params, "detenida_mas_de_dias", minimo=0
            )
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)

        pagina = InformesRegionService().regiones(
            cursor=cursor,
            limit=limit,
            orden=orden,
            estado_region=estado,
            detenida_mas_de_dias=detenida,
        )
        return listado_response(
            pagina,
            {"estado_region": estado, "detenida_mas_de_dias": detenida},
            # Siempre `todos`: no hay eje de titularidad que acotar. Se declara
            # igualmente porque el contrato lo exige en los cuatro listados.
            acotado_a=ACOTADO_TODOS,
        )


class ValidacionesRegionView(ListadoBaseView):
    """L4 — historial completo de intentos. **Ninguno sustituye a otro.**"""

    permission_classes = [IsAuthenticated401, InformesValidacionPermission]
    admite_rango = True

    def get(self, request: Request):
        try:
            periodo, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_VALIDACIONES)
            cursor = CURSOR_VALIDACIONES.decodificar(request.query_params.get("cursor"))
            idregion = self.parse_entero(request.query_params, "region", minimo=1)

            servicio = InformesRegionService()
            resultado = request.query_params.get("resultado") or None
            if resultado is not None:
                validos = servicio.resultados_disponibles()
                if resultado not in validos:
                    raise FiltroInvalido(
                        f"El filtro 'resultado' no admite el valor '{resultado}'; "
                        f"use uno de: {', '.join(validos)}."
                    )
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)

        pagina = servicio.validaciones(
            cursor=cursor,
            limit=limit,
            orden=orden,
            idregion=idregion,
            resultado=resultado,
            desde_ms=periodo.desde_ms,
            hasta_ms=periodo.hasta_ms,
        )
        return listado_response(
            pagina,
            {**periodo.to_meta(), "region": idregion, "resultado": resultado},
            acotado_a=ACOTADO_TODOS,
        )
