"""Vistas de los cinco listados tácticos de Partners y API.

**Este módulo no reescribe el acotamiento.** `verificar_propiedad` ya resuelve
la cuenta del solicitante —con el mismo servicio que usa Soporte—, exime a los
gestores y **lanza en vez de devolver un booleano**, para que sea imposible
ignorar el resultado por descuido. Los listados lo reutilizan tal cual.

El detalle de que **lance** es el que conviene conservar: un `if not
verificar(...)` olvidado es un fallo silencioso de autorización, y una excepción
no se puede ignorar sin querer.
"""

from __future__ import annotations

from rest_framework.request import Request

from apps.partners.domain_constants import (
    ENTORNOS,
    ESTADO_PENDIENTE_APROBACION,
    ESTADO_PLAN_ASIGNADO,
    ESTADO_PRODUCCION_ACTIVA,
    ESTADO_PRUEBAS_ACTIVO,
    ESTADO_REGISTRADO,
    ESTADO_SUSPENDIDO,
    ESTADOS_VERSION,
)
from apps.partners.permissions import (
    InformesAccesoPermission,
    InformesContratoPermission,
    PropiedadPartnerError,
    es_gestor_informes,
)
from apps.partners.services.informes_acceso_service import InformesAccesoService
from apps.partners.services.informes_bitacora_service import InformesBitacoraService
from apps.partners.services.informes_contrato_service import InformesContratoService
from core.auth.permissions import IsAuthenticated401
from core.informes.acotamiento import (
    ACOTADO_PROPIOS,
    ACOTADO_TODOS,
    Acotamiento,
)
from core.api.response_envelope import success_response
from core.informes.catalogos import TOPE_CATALOGO, CatalogosFiltrosRepository
from core.informes.envelope import listado_response
from core.informes.paginacion import parse_dir
from core.informes.vistas import ERRORES_DE_VALIDACION, FiltroInvalido, ListadoBaseView
from core.repositories.partners.informes_acceso_repository import (
    CURSOR_CREDENCIALES,
    CURSOR_PARTNERS,
    ORDEN_CREDENCIALES,
    ORDEN_PARTNERS,
)
from core.repositories.partners.informes_bitacora_repository import (
    CURSOR_BITACORA,
    ORDEN_BITACORA,
)
from core.repositories.partners.informes_contrato_repository import (
    CURSOR_ALCANCE,
    CURSOR_VERSIONES,
    ORDEN_ALCANCE,
    ORDEN_VERSIONES,
)

#: Los seis estados, **importados del dominio**, no copiados (research D5).
#: Copiarlos crearía dos fuentes de verdad: el día que se añada un estado, el
#: filtro lo rechazaría con un `400` engañoso —«no es válido»— cuando sí lo es.
ESTADOS_PARTNER = (
    ESTADO_REGISTRADO,
    ESTADO_PLAN_ASIGNADO,
    ESTADO_PRUEBAS_ACTIVO,
    ESTADO_PENDIENTE_APROBACION,
    ESTADO_PRODUCCION_ACTIVA,
    ESTADO_SUSPENDIDO,
)


class _ListadoAccesoView(ListadoBaseView):
    """Base de los tres listados que un partner puede ver, acotado a lo suyo."""

    permission_classes = [IsAuthenticated401, InformesAccesoPermission]

    def acotar(self, request: Request) -> Acotamiento:
        """Reutiliza el mecanismo de propiedad del módulo, sin modificarlo.

        Un gestor no se acota. Un partner queda forzado a su cuenta, resuelta
        por el mismo servicio que usa Soporte.
        """
        pedido = self.parse_entero(request.query_params, "partner", minimo=1)

        if es_gestor_informes(request):
            # Puede filtrar por un partner concreto sin que eso reduzca su
            # alcance declarado: sigue teniendo acceso a todos.
            return Acotamiento(titular=None, alcance=ACOTADO_TODOS)

        from apps.soporte_cliente.services.cliente_lookup_service import (
            ClienteLookupService,
        )

        idusuario = getattr(request.user, "idusuario", None)
        idcliente = ClienteLookupService().resolve_idcliente(int(idusuario))
        if idcliente is None:
            raise PropiedadPartnerError(
                "El solicitante no pertenece a ninguna cuenta cliente."
            )

        if pedido is not None:
            # Pedir un partner concreto siendo partner: se comprueba que sea
            # suyo con el mecanismo del módulo, que **lanza** si no lo es.
            from core.repositories.partners.partner_repository import PartnerRepository

            partner = PartnerRepository().find_by_id(pedido)
            from apps.partners.permissions import verificar_propiedad

            verificar_propiedad(request, partner)

        return Acotamiento(titular=int(idcliente), alcance=ACOTADO_PROPIOS)

    @staticmethod
    def manejar_propiedad(exc: PropiedadPartnerError):
        from core.api.response_envelope import error_response

        return error_response("forbidden", str(exc), "403", status_code=403)


class PartnersView(_ListadoAccesoView):
    """L1 — partners con su estado de incorporación."""

    admite_rango = False

    def get(self, request: Request):
        try:
            _, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_PARTNERS)
            cursor = CURSOR_PARTNERS.decodificar(request.query_params.get("cursor"))
            estado = self.parse_enumeracion(
                request.query_params, "estado", ESTADOS_PARTNER
            )
            plan = request.query_params.get("plan") or None
            # ⚠️ Se leía y se **descartaba**: el desplegable «Partner» estaba en
            # pantalla, el parámetro viajaba, y el listado devolvía todos los
            # partners igual. `acotar()` lo lee para comprobar propiedad, no
            # para filtrar, y `acotamiento.titular` es `None` en un gestor.
            idpartner = self.parse_entero(request.query_params, "partner", minimo=1)
            acotamiento = self.acotar(request)
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)
        except PropiedadPartnerError as exc:
            return self.manejar_propiedad(exc)

        pagina = InformesAccesoService().partners(
            acotamiento=acotamiento,
            cursor=cursor,
            limit=limit,
            orden=orden,
            estado=estado,
            plan=plan,
            idpartner=idpartner,
        )
        return listado_response(
            pagina,
            {"estado": estado, "plan": plan, "partner": idpartner},
            acotado_a=acotamiento.alcance,
        )


class CredencialesView(_ListadoAccesoView):
    """L2 — credenciales. ⛔ El secreto de autenticación no sale."""

    admite_rango = False

    def get(self, request: Request):
        try:
            _, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_CREDENCIALES)
            cursor = CURSOR_CREDENCIALES.decodificar(request.query_params.get("cursor"))
            entorno = self.parse_enumeracion(
                request.query_params, "entorno", sorted(ENTORNOS)
            )
            activa = self.parse_booleano(request.query_params, "activa")
            caduca = self.parse_entero(request.query_params, "caduca_en_dias", minimo=0)
            idpartner = self.parse_entero(request.query_params, "partner", minimo=1)
            acotamiento = self.acotar(request)
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)
        except PropiedadPartnerError as exc:
            return self.manejar_propiedad(exc)

        pagina = InformesAccesoService().credenciales(
            acotamiento=acotamiento,
            cursor=cursor,
            limit=limit,
            orden=orden,
            idpartner=idpartner,
            entorno=entorno,
            activa=activa,
            caduca_en_dias=caduca,
        )
        return listado_response(
            pagina,
            {
                "entorno": entorno,
                "activa": activa,
                "caduca_en_dias": caduca,
                "partner": idpartner,
            },
            acotado_a=acotamiento.alcance,
        )


class CambiosAccesoView(_ListadoAccesoView):
    """L3 — la bitácora donde **sí** viven los motivos."""

    admite_rango = True

    def get(self, request: Request):
        try:
            periodo, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_BITACORA)
            cursor = CURSOR_BITACORA.decodificar(request.query_params.get("cursor"))
            idpartner = self.parse_entero(request.query_params, "partner", minimo=1)

            tipo = request.query_params.get("tipo_cambio") or None
            if tipo is not None:
                # Contra las constantes **importadas** del dominio: un tipo
                # nuevo no debe producir un `400` engañoso desde aquí.
                from apps.partners import domain_constants

                validos = sorted(
                    v for k, v in vars(domain_constants).items()
                    if k.startswith("CAMBIO_") and isinstance(v, str)
                )
                if tipo not in validos:
                    raise FiltroInvalido(
                        f"El filtro 'tipo_cambio' no admite el valor '{tipo}'; "
                        f"use uno de: {', '.join(validos)}."
                    )

            acotamiento = self.acotar(request)
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)
        except PropiedadPartnerError as exc:
            return self.manejar_propiedad(exc)

        pagina = InformesBitacoraService().cambios(
            acotamiento=acotamiento,
            cursor=cursor,
            limit=limit,
            orden=orden,
            idpartner=idpartner,
            tipo_cambio=tipo,
            desde_ms=periodo.desde_ms,
            hasta_ms=periodo.hasta_ms,
        )
        return listado_response(
            pagina,
            {**periodo.to_meta(), "tipo_cambio": tipo, "partner": idpartner},
            acotado_a=acotamiento.alcance,
        )


class _ListadoContratoView(ListadoBaseView):
    """Base de los dos listados de gestor. **Sin acotamiento** (FR-013)."""

    permission_classes = [IsAuthenticated401, InformesContratoPermission]
    admite_rango = False


class VersionesContratoView(_ListadoContratoView):
    """L4 — versiones del contrato, **incluidas las retiradas** (FR-004)."""

    def get(self, request: Request):
        try:
            _, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_VERSIONES)
            cursor = CURSOR_VERSIONES.decodificar(request.query_params.get("cursor"))
            estado = self.parse_enumeracion(
                request.query_params, "estado", sorted(ESTADOS_VERSION)
            )
            servicio = self.parse_entero(request.query_params, "servicio", minimo=1)
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)

        pagina = InformesContratoService().versiones(
            cursor=cursor, limit=limit, orden=orden, estado=estado, id_servicio=servicio
        )
        return listado_response(
            pagina,
            {"estado": estado, "servicio": servicio},
            acotado_a=ACOTADO_TODOS,
        )


class AlcanceDatosView(_ListadoContratoView):
    """L5 — alcance contratado. ⚠️ Sin configurar **no** es acceso ilimitado."""

    def get(self, request: Request):
        try:
            _, limit = self.parse_peticion(request)
            orden = parse_dir(request.query_params, por_defecto=ORDEN_ALCANCE)
            cursor = CURSOR_ALCANCE.decodificar(request.query_params.get("cursor"))
            cuenta = self.parse_entero(request.query_params, "cuenta", minimo=1)
            frecuencia = request.query_params.get("frecuencia") or None
        except ERRORES_DE_VALIDACION as exc:
            return self.manejar_peticion_invalida(exc)

        pagina = InformesContratoService().alcance(
            cursor=cursor,
            limit=limit,
            orden=orden,
            id_cliente=cuenta,
            frecuencia=frecuencia,
        )
        return listado_response(
            pagina,
            {"cuenta": cuenta, "frecuencia": frecuencia},
            acotado_a=ACOTADO_TODOS,
        )


class _CatalogosBaseView(ListadoBaseView):
    """Base de los catálogos que pueblan los desplegables de estos listados.

    ⚠️ **Comparten el permiso y el acotamiento de su listado, y no por simetría.**
    La lista de partners no es una fila del listado, es metadato, así que el
    acotamiento por propiedad no la cubre sola: hay que aplicarla a mano. Un
    catálogo completo diría a un partner **quién más integra la plataforma**, y
    lo diría con su listado devolviendo exactamente lo de siempre.
    """

    def _permitidos(self, request: Request) -> frozenset[int] | None:
        """Partners que el solicitante puede ver, o `None` si son todos.

        Un gestor no se acota. A un partner se le resuelve su cuenta con el
        mismo servicio que usa el listado, y de ahí sus partners: `None` aquí
        sería el catálogo entero, que es justo lo que no puede ver.
        """
        if es_gestor_informes(request):
            return None

        from apps.soporte_cliente.services.cliente_lookup_service import (
            ClienteLookupService,
        )

        idusuario = getattr(request.user, "idusuario", None)
        idcliente = ClienteLookupService().resolve_idcliente(int(idusuario))
        if idcliente is None:
            # Sin cuenta no hay partners suyos: **cero opciones**, no todas.
            return frozenset()

        from core.repositories.partners.informes_acceso_repository import (
            InformesAccesoRepository,
        )

        filas = InformesAccesoRepository().partners(
            cuenta=int(idcliente), limit=TOPE_CATALOGO
        )
        return frozenset(
            f["idpartner"] for f in filas if f.get("idpartner") is not None
        )


class CatalogosAccesoView(_CatalogosBaseView):
    """Opciones del filtro «Partner» de los tres listados de acceso."""

    permission_classes = [IsAuthenticated401, InformesAccesoPermission]

    def get(self, request: Request):
        try:
            permitidos = self._permitidos(request)
        except PropiedadPartnerError as exc:
            return self.manejar_propiedad(exc)

        repo = CatalogosFiltrosRepository()
        return success_response(
            {"partner": repo.partners(permitidos)},
            meta={"acotado_a": ACOTADO_TODOS if permitidos is None else ACOTADO_PROPIOS},
        )


class CatalogosContratoView(_CatalogosBaseView):
    """Opciones de «Servicio» y «Cuenta» de los dos listados de contrato.

    Solo entran gestores (FR-013), así que no hay acotamiento que aplicar: el
    alcance de datos describe lo que cada **cliente** tiene contratado, y las
    versiones gobiernan el ciclo de vida del contrato.
    """

    permission_classes = [IsAuthenticated401, InformesContratoPermission]

    def get(self, request: Request):
        repo = CatalogosFiltrosRepository()
        return success_response(
            {"servicio": repo.servicios(), "cuenta": repo.clientes(None)},
            meta={"acotado_a": ACOTADO_TODOS},
        )
