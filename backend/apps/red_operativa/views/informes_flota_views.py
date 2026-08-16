"""Vista de la composición de la flota — L1 de OT12.

⚠️ **La respuesta declara su propio alcance** (FR-008), y es la razón de que este
campo exista en el envelope transversal.

`dado_de_alta` significa que la unidad **existe**, no que pueda acudir. Un
consumidor que lea este listado como cobertura disponible decidiría sobre
unidades fuera de servicio, ocupadas o ya en camino a otro accidente. En los
módulos comerciales un error así infla una cifra; aquí decide si alguien acude.

La disponibilidad real es CU-T08, compuesta, y va sobre el modelo analítico.
"""

from __future__ import annotations

from rest_framework.request import Request

from apps.red_operativa.permissions import (
    AMPLIOS_FLOTA,
    ROLES_INFORMES_FLOTA_ACOTADOS,
    InformesFlotaPermission,
)
from apps.red_operativa.services.informes_flota_service import InformesFlotaService
from apps.red_operativa.views.informes_base import ListadoRedOperativaBaseView
from core.auth.permissions import IsAuthenticated401
from core.informes.acotamiento import AccesoDenegado
from core.informes.envelope import listado_response
from core.informes.paginacion import parse_dir
from core.informes.vistas import ERRORES_DE_VALIDACION, FiltroInvalido
from core.repositories.red_operativa.informes_flota_repository import (
    ALCANCE_COMPOSICION,
    CURSOR_FLOTA,
    ORDEN_FLOTA,
)


class FlotaView(ListadoRedOperativaBaseView):
    permission_classes = [IsAuthenticated401, InformesFlotaPermission]
    admite_rango = False
    roles_amplios = AMPLIOS_FLOTA
    roles_acotados = ROLES_INFORMES_FLOTA_ACOTADOS

    def get(self, request: Request):
        try:
            _, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_FLOTA)
            cursor = CURSOR_FLOTA.decodificar(request.query_params.get("cursor"))
            idcondado = self.parse_entero(request.query_params, "condado", minimo=1)
            dado_de_alta = self.parse_booleano(request.query_params, "dado_de_alta")

            servicio = InformesFlotaService()
            tipo = request.query_params.get("tipo_unidad") or None
            if tipo is not None:
                # Contra los tipos que existen en los datos: el catálogo de
                # tipos de unidad no vive en ninguna dimensión, y una lista fija
                # rechazaría un tipo nuevo con `400`.
                validos = servicio.tipos_disponibles()
                if tipo not in validos:
                    raise FiltroInvalido(
                        f"El filtro 'tipo_unidad' no admite el valor '{tipo}'; "
                        f"use uno de: {', '.join(validos)}."
                    )

            acotamiento = self.acotar(request)
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)
        except AccesoDenegado as exc:
            return self.manejar_acceso_denegado(exc)

        pagina = servicio.flota(
            acotamiento=acotamiento,
            cursor=cursor,
            limit=limit,
            orden=orden,
            idcondado=idcondado,
            tipo_unidad=tipo,
            dado_de_alta=dado_de_alta,
        )
        return listado_response(
            pagina,
            {
                "condado": idcondado,
                "tipo_unidad": tipo,
                "dado_de_alta": dado_de_alta,
                "proveedor": acotamiento.titular,
            },
            acotado_a=acotamiento.alcance,
            # La advertencia va **en la respuesta**, no solo en la
            # documentación: un consumidor puede no haber leído la spec.
            alcance=ALCANCE_COMPOSICION,
        )
