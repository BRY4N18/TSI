"""Vistas de los listados tácticos de Emergencias servidos por esta app.

Casos, fotografías de evidencia, notas de campo y cierres. Los despachos viven
en `apps/seguimiento` porque su tabla es la que ese módulo opera.

⚠️ El eje de acotamiento es nuevo: **cobertura contratada**
------------------------------------------------------------
Los tres anteriores acotan por titularidad. Aquí un Cliente no ve «sus»
accidentes —no son suyos en ningún sentido—: ve los de las zonas que contrató, y
**solo los ya cerrados**. Por eso `meta.acotado_a` toma un valor propio,
`zonas_contratadas`: decir `propios` afirmaría algo falso.
"""

from __future__ import annotations

from rest_framework.request import Request

from apps.accidentes.permissions import (
    InformesCasosPermission,
    InformesEmergenciasInternoPermission,
    ROLES_CLIENTE_EMERGENCIAS,
    ROLES_INTERNOS_EMERGENCIAS,
)
from apps.accidentes.services.informes_casos_service import InformesCasosService
from apps.accidentes.services.informes_catalogos_service import (
    InformesCatalogosService,
)
from apps.accidentes.services.informes_cierres_service import InformesCierresService
from apps.accidentes.services.informes_evidencia_service import (
    InformesEvidenciaService,
)
from core.auth.permissions import IsAuthenticated401
from core.informes.acotamiento import ACOTADO_TODOS, AccesoDenegado
from core.informes.cobertura import resolver_cobertura
from core.api.response_envelope import success_response
from core.informes.envelope import listado_response
from core.informes.paginacion import parse_dir
from core.informes.vistas import ERRORES_DE_VALIDACION, ListadoBaseView
from core.repositories.accidentes.informes_casos_repository import (
    CURSOR_CASOS,
    ORDEN_CASOS,
    SITUACIONES,
)
from core.repositories.accidentes.informes_cierres_repository import (
    CURSOR_CIERRES,
    ORDEN_CIERRES,
)
from core.repositories.accidentes.informes_evidencia_repository import (
    CURSOR_FOTOS,
    CURSOR_NOTAS,
    ORDEN_EVIDENCIA,
)
from core.repositories.accidentes.informes_ubicacion_repository import (
    InformesUbicacionRepository,
)


class CasosView(ListadoBaseView):
    """L1 — casos del período, acotados por cobertura contratada."""

    permission_classes = [IsAuthenticated401, InformesCasosPermission]
    admite_rango = True

    def get(self, request: Request):
        try:
            periodo, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_CASOS)
            cursor = CURSOR_CASOS.decodificar(request.query_params.get("cursor"))
            severidad = self.parse_entero(request.query_params, "severidad", minimo=1)
            condado = self.parse_entero(request.query_params, "condado", minimo=1)
            ciudad = self.parse_entero(request.query_params, "ciudad", minimo=1)
            tipo = self.parse_entero(
                request.query_params, "tipo_reportado", minimo=1
            )
            situacion = self.parse_enumeracion(
                request.query_params, "situacion", SITUACIONES
            )

            cobertura = resolver_cobertura(
                roles=getattr(request.user, "roles", []) or [],
                user_id=request.user.idusuario,
                roles_internos=ROLES_INTERNOS_EMERGENCIAS,
                roles_cliente=ROLES_CLIENTE_EMERGENCIAS,
                resolver_ubicaciones=_zonas_del_cliente,
            )
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)
        except AccesoDenegado as exc:
            return self.manejar_acceso_denegado(exc)

        pagina = InformesCasosService().casos(
            cobertura=cobertura,
            cursor=cursor,
            limit=limit,
            orden=orden,
            idseveridad=severidad,
            idtiporeportado=tipo,
            idcondado=condado,
            idciudad=ciudad,
            situacion=situacion,
            desde_ms=periodo.desde_ms,
            hasta_ms=periodo.hasta_ms,
        )
        return listado_response(
            pagina,
            {
                **periodo.to_meta(),
                "severidad": severidad,
                "condado": condado,
                "ciudad": ciudad,
                "tipo_reportado": tipo,
                # Si el eje la impuso, se declara: un cliente debe poder ver en
                # `meta` por qué no le llegan los casos en curso.
                "situacion": "cerrado" if cobertura.solo_cerrados else situacion,
            },
            acotado_a=cobertura.alcance,
        )


class CatalogosCasosView(ListadoBaseView):
    """Opciones de los desplegables del listado de casos.

    Existe porque los filtros pedían identificadores numéricos a mano —«Condado
    (id)»— y la tabla solo mostraba nombres: no había manera de averiguar el
    número desde la propia pantalla.

    ⚠️ **Comparte el permiso y el acotamiento del listado, y no por simetría.**
    La lista de condados es metadato, no filas, así que `Cobertura` no la cubre
    por sí sola: hay que aplicarla a mano. Un catálogo completo diría dónde opera
    el sistema a quien contrató una zona, y lo diría con el listado devolviendo
    cero filas — sin ningún síntoma.
    """

    permission_classes = [IsAuthenticated401, InformesCasosPermission]

    def get(self, request: Request):
        try:
            cobertura = resolver_cobertura(
                roles=getattr(request.user, "roles", []) or [],
                user_id=request.user.idusuario,
                roles_internos=ROLES_INTERNOS_EMERGENCIAS,
                roles_cliente=ROLES_CLIENTE_EMERGENCIAS,
                resolver_ubicaciones=_zonas_del_cliente,
            )
        except AccesoDenegado as exc:
            return self.manejar_acceso_denegado(exc)

        catalogos = InformesCatalogosService().catalogos(cobertura=cobertura)
        return success_response(catalogos, meta={"acotado_a": cobertura.alcance})


class _ListadoInternoView(ListadoBaseView):
    """Base de los tres listados que solo ven los roles internos (FR-013)."""

    permission_classes = [IsAuthenticated401, InformesEmergenciasInternoPermission]


class EvidenciaFotosView(_ListadoInternoView):
    """L3 — fotografías. ⚠️ La hora de captura es la del sitio."""

    admite_rango = True

    def get(self, request: Request):
        try:
            periodo, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_EVIDENCIA)
            cursor = CURSOR_FOTOS.decodificar(request.query_params.get("cursor"))
            sincronizado = self.parse_booleano(request.query_params, "sincronizado")
            caso = request.query_params.get("caso") or None
            autor = self.parse_entero(request.query_params, "autor", minimo=1)
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)

        pagina = InformesEvidenciaService().fotos(
            cursor=cursor,
            limit=limit,
            orden=orden,
            sincronizado=sincronizado,
            idaccidente=caso,
            idusuario=autor,
            desde_ms=periodo.desde_ms,
            hasta_ms=periodo.hasta_ms,
        )
        return listado_response(
            pagina,
            {**periodo.to_meta(), "sincronizado": sincronizado,
             "caso": caso, "autor": autor},
            acotado_a=ACOTADO_TODOS,
        )


class NotasCampoView(_ListadoInternoView):
    """L4 — notas de campo. ⚠️ La hora de registro sale de otra columna."""

    admite_rango = True

    def get(self, request: Request):
        try:
            periodo, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_EVIDENCIA)
            cursor = CURSOR_NOTAS.decodificar(request.query_params.get("cursor"))
            sincronizado = self.parse_booleano(request.query_params, "sincronizado")
            tipo = request.query_params.get("tipo") or None
            caso = request.query_params.get("caso") or None
            autor = self.parse_entero(request.query_params, "autor", minimo=1)
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)

        pagina = InformesEvidenciaService().notas(
            cursor=cursor,
            limit=limit,
            orden=orden,
            sincronizado=sincronizado,
            tipo=tipo,
            idaccidente=caso,
            idusuario=autor,
            desde_ms=periodo.desde_ms,
            hasta_ms=periodo.hasta_ms,
        )
        return listado_response(
            pagina,
            {**periodo.to_meta(), "sincronizado": sincronizado, "tipo": tipo,
             "caso": caso, "autor": autor},
            acotado_a=ACOTADO_TODOS,
        )


class CierresView(_ListadoInternoView):
    """L5 — cierres. **Estado actual**: la tabla no tiene fecha propia."""

    admite_rango = False

    def get(self, request: Request):
        try:
            _, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_CIERRES)
            cursor = CURSOR_CIERRES.decodificar(request.query_params.get("cursor"))
            resultado = request.query_params.get("resultado") or None
            sin_obs = self.parse_booleano(
                request.query_params, "sin_observaciones"
            )
            con_cal = self.parse_booleano(
                request.query_params, "con_calificacion"
            )
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)

        pagina = InformesCierresService().cierres(
            cursor=cursor,
            limit=limit,
            orden=orden,
            resultado=resultado,
            sin_observaciones=sin_obs,
            con_calificacion=con_cal,
        )
        return listado_response(
            pagina,
            {"resultado": resultado, "sin_observaciones": sin_obs,
             "con_calificacion": con_cal},
            acotado_a=ACOTADO_TODOS,
        )


def _zonas_del_cliente(idusuario: int) -> frozenset[int]:
    """Condados contratados por la cuenta del solicitante.

    ⚠️ Devuelve conjunto **vacío** cuando no hay cuenta o no hay zonas, y vacío
    significa cero resultados. Fallar abierto aquí daría el mapa de
    siniestralidad completo a quien no contrató nada.
    """
    from apps.soporte_cliente.services.cliente_lookup_service import (
        ClienteLookupService,
    )

    idcliente = ClienteLookupService().resolve_idcliente(int(idusuario))
    if idcliente is None:
        return frozenset()
    return InformesUbicacionRepository().zonas_contratadas(int(idcliente))


class CatalogosEvidenciaView(_ListadoInternoView):
    """Opciones del filtro «Autor» de fotografías y notas de campo.

    Solo roles internos, igual que sus listados: quién levantó la evidencia es
    operación interna, y el catálogo no puede decir más que el listado.
    """

    def get(self, request: Request):
        from core.informes.catalogos import CatalogosFiltrosRepository

        return success_response(
            {"autor": CatalogosFiltrosRepository().usuarios(None)},
            meta={"acotado_a": ACOTADO_TODOS},
        )
