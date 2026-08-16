"""Vista de las reasignaciones de cartera — L2 de OT02 / CU-O19.

Es de **hechos del período**: acepta `desde`/`hasta` **opcionales**, y omitirlos
devuelve el histórico completo paginado. Es el primer listado del departamento
con esa forma; los otros tres son de estado actual.

Y es el único **sin acotamiento**: solo accede el rol amplio. Un gerente no lo ve
ni siquiera acotado a lo suyo, porque el reparto de cartera es una decisión sobre
él, no una herramienta suya.
"""

from __future__ import annotations

from rest_framework.request import Request

from apps.ventas_crm.permissions import InformesReasignacionesPermission
from apps.ventas_crm.services.informes_asignacion_service import (
    InformesAsignacionService,
)
from core.auth.permissions import IsAuthenticated401
from core.informes.acotamiento import ACOTADO_TODOS
from core.informes.envelope import listado_response
from core.informes.paginacion import parse_dir
from core.informes.vistas import ERRORES_DE_VALIDACION, FiltroInvalido, ListadoBaseView
from core.repositories.ventas_crm.informes_asignacion_repository import (
    CURSOR_ASIGNACIONES,
    ORDEN_ASIGNACIONES,
)


class ReasignacionesView(ListadoBaseView):
    permission_classes = [IsAuthenticated401, InformesReasignacionesPermission]
    admite_rango = True

    def get(self, request: Request):
        try:
            periodo, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_ASIGNACIONES)
            cursor = CURSOR_ASIGNACIONES.decodificar(request.query_params.get("cursor"))
            idprospecto = self.parse_entero(request.query_params, "idprospecto", minimo=1)

            servicio = InformesAsignacionService()
            tipo = request.query_params.get("tipo_asignacion") or None
            if tipo is not None:
                # Contra los tipos que existen en los datos, no contra una lista
                # fija: el catálogo no vive en ninguna dimensión.
                validos = servicio.tipos_disponibles()
                if tipo not in validos:
                    raise FiltroInvalido(
                        f"El filtro 'tipo_asignacion' no admite el valor '{tipo}'; "
                        f"use uno de: {', '.join(validos)}."
                    )
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)

        pagina = servicio.reasignaciones(
            cursor=cursor,
            limit=limit,
            orden=orden,
            desde_ms=periodo.desde_ms,
            hasta_ms=periodo.hasta_ms,
            idprospecto=idprospecto,
            tipo_asignacion=tipo,
        )
        return listado_response(
            pagina,
            {**periodo.to_meta(), "idprospecto": idprospecto, "tipo_asignacion": tipo},
            # Siempre `todos`: aquí solo llega el rol amplio y no hay eje de
            # titularidad. Se declara igualmente porque el contrato lo exige en
            # los cuatro listados, y omitirlo obligaría al consumidor a saber
            # cuál de ellos es la excepción.
            acotado_a=ACOTADO_TODOS,
        )
