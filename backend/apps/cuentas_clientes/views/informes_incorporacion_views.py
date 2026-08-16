"""Vistas de los dos listados de OT04 — incorporacion de clientes nuevos.

Ambos son de **estado actual**: describen que esta detenido *ahora*. El rango de
fechas se rechaza con `400` (FR-012); lo que si aceptan es `dias_minimo`, que no
es un rango sino un umbral de antiguedad y se resuelve contra el reloj.

`tipo` no se valida contra una lista cerrada
--------------------------------------------
El OpenAPI declara `enum: [aseguradora, municipio, proveedor]`, pero los valores
reales de `Dim_Cliente.tipo` son otros —`Corporativo`, `Proveedor`—. Validar
contra el enum del contrato rechazaria con `400` un `tipo=Corporativo`
perfectamente valido, que es peor que no validar: un filtro correcto devolveria
error. Se trata como filtro de igualdad libre y **se corrige el contrato**.
"""

from __future__ import annotations

from rest_framework.request import Request

from apps.cuentas_clientes.permissions import InformesCuentasLecturaPermission
from apps.cuentas_clientes.services.informes_incorporacion_service import (
    InformesIncorporacionService,
)
from core.auth.permissions import IsAuthenticated401
from core.informes.envelope import listado_response
from core.informes.paginacion import parse_dir
from core.informes.vistas import ERRORES_DE_VALIDACION, FiltroInvalido, ListadoBaseView
from core.repositories.cuentas_clientes.informes_incorporacion_repository import (
    CURSOR_ONBOARDING,
    CURSOR_SOLICITUDES,
    ORDEN_ONBOARDING,
    ORDEN_SOLICITUDES,
)


class _ListadoIncorporacionView(ListadoBaseView):
    permission_classes = [IsAuthenticated401, InformesCuentasLecturaPermission]
    admite_rango = False

    def servicio(self) -> InformesIncorporacionService:
        return InformesIncorporacionService()


class SolicitudesAltaPendientesView(_ListadoIncorporacionView):
    """L1 — bandeja de solicitudes esperando aprobacion, con su antiguedad."""

    def get(self, request: Request):
        try:
            _, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_SOLICITUDES)
            cursor = CURSOR_SOLICITUDES.decodificar(request.query_params.get("cursor"))
            tipo = request.query_params.get("tipo") or None
            dias_minimo = self.parse_entero(request.query_params, "dias_minimo", minimo=0)
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)

        pagina = self.servicio().solicitudes_pendientes(
            cursor=cursor, limit=limit, orden=orden, tipo=tipo, dias_minimo=dias_minimo
        )
        return listado_response(pagina, {"tipo": tipo, "dias_minimo": dias_minimo})


class OnboardingIncompletoView(_ListadoIncorporacionView):
    """L2 — una fila por etapa de incorporacion pendiente (research D6)."""

    def get(self, request: Request):
        try:
            _, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_ONBOARDING)
            cursor = CURSOR_ONBOARDING.decodificar(request.query_params.get("cursor"))
            dias_minimo = self.parse_entero(request.query_params, "dias_minimo", minimo=0)

            servicio = self.servicio()
            etapa = request.query_params.get("etapa") or None
            if etapa is not None:
                # Contra las etapas que existen en los datos, no contra una
                # lista fija: el catalogo de etapas no vive en ninguna dimension
                # y una lista escrita a mano rechazaria una etapa nueva.
                validas = servicio.etapas_disponibles()
                if etapa not in validas:
                    raise FiltroInvalido(
                        f"El filtro 'etapa' no admite el valor '{etapa}'; "
                        f"use uno de: {', '.join(validas)}."
                    )
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)

        pagina = servicio.onboarding_incompleto(
            cursor=cursor, limit=limit, orden=orden, etapa=etapa, dias_minimo=dias_minimo
        )
        return listado_response(pagina, {"etapa": etapa, "dias_minimo": dias_minimo})
