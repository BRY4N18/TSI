"""Vista del listado táctico de despachos — L2 de OT22/OT23.

Vive en esta app y no en `accidentes` porque `Fact_Despacho` es la tabla que
Seguimiento opera. Los permisos, en cambio, se **importan** de `accidentes`: los
cinco listados del departamento comparten un mismo mapa de roles, y duplicarlo
aquí crearía dos fuentes de verdad que divergirían al primer rol nuevo.
"""

from __future__ import annotations

from rest_framework.request import Request

from apps.accidentes.permissions import InformesEmergenciasInternoPermission
from apps.seguimiento.services.informes_despachos_service import (
    InformesDespachosService,
)
from core.auth.permissions import IsAuthenticated401
from core.informes.acotamiento import ACOTADO_TODOS
from core.informes.envelope import listado_response
from core.informes.paginacion import parse_dir
from core.informes.vistas import ERRORES_DE_VALIDACION, ListadoBaseView
from core.repositories.seguimiento.informes_despachos_repository import (
    CURSOR_DESPACHOS,
    ORDEN_DESPACHOS,
)


class DespachosView(ListadoBaseView):
    """Despachos del período. **Solo roles internos** (FR-013)."""

    permission_classes = [IsAuthenticated401, InformesEmergenciasInternoPermission]
    admite_rango = True

    def get(self, request: Request):
        try:
            periodo, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_DESPACHOS)
            cursor = CURSOR_DESPACHOS.decodificar(request.query_params.get("cursor"))
            origen = self.parse_entero(request.query_params, "origen", minimo=1)
            unidad = self.parse_entero(request.query_params, "unidad", minimo=1)
            caso = request.query_params.get("caso") or None
            en_transito = self.parse_booleano(request.query_params, "en_transito")
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)

        pagina = InformesDespachosService().despachos(
            cursor=cursor,
            limit=limit,
            orden=orden,
            idorigendespacho=origen,
            idunidademergencia=unidad,
            idaccidente=caso,
            en_transito=en_transito,
            desde_ms=periodo.desde_ms,
            hasta_ms=periodo.hasta_ms,
        )
        return listado_response(
            pagina,
            {**periodo.to_meta(), "origen": origen, "unidad": unidad,
             "caso": caso, "en_transito": en_transito},
            acotado_a=ACOTADO_TODOS,
        )


class CatalogosDespachosView(ListadoBaseView):
    """Opciones de «Origen» y «Unidad» del listado de despachos.

    Mismo permiso interno que el listado: qué unidad atendió qué caso es
    operación interna, y el catálogo no puede decir más que la tabla.
    """

    permission_classes = [IsAuthenticated401, InformesEmergenciasInternoPermission]
    admite_rango = False

    def get(self, request: Request):
        from core.api.response_envelope import success_response
        from core.informes.catalogos import CatalogosFiltrosRepository

        repo = CatalogosFiltrosRepository()
        return success_response(
            {"origen": repo.origenes_despacho(), "unidad": repo.unidades()},
            meta={"acotado_a": ACOTADO_TODOS},
        )
