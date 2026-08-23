"""DRF permissions de Partners y API (CU-O48 a CU-O55).

Incluye la comprobacion de PROPIEDAD (`partner_del_token`), que no es un
permiso DRF sino una guarda de servicio: verifica que el partner sobre el que
se opera pertenece al cliente del token.

Se omitio por error en Red Operativa, Emergencias y en tres endpoints de
Soporte (`decisiones-pendientes.md` #14). Aqui se centraliza para que ningun
endpoint de autoservicio pueda olvidarla.
"""

from __future__ import annotations

from typing import Any

from rest_framework.permissions import BasePermission

from apps.partners.domain_constants import (
    ROL_ADMINISTRADOR,
    ROL_DESARROLLADOR_APIS,
    ROL_DIRECTOR_TECNOLOGICO,
    ROL_PARTNER_INTEGRACION,
)


def _roles(request) -> set[str]:
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return set()
    return set(getattr(user, "roles", []) or [])


class EsAdministrador(BasePermission):
    """Solo Administrador. Resolucion de la promocion a produccion (RF-PON-008)."""

    def has_permission(self, request, view) -> bool:
        return ROL_ADMINISTRADOR in _roles(request)


class EsDesarrolladorAPIs(BasePermission):
    """Desarrollador de APIs o Administrador — registro y asignacion de plan."""

    def has_permission(self, request, view) -> bool:
        return bool(_roles(request) & {ROL_DESARROLLADOR_APIS, ROL_ADMINISTRADOR})


class EsPartner(BasePermission):
    """Partner de integracion — autoservicio sobre SU PROPIO perfil.

    El permiso solo comprueba el rol. La pertenencia del `idpartner` concreto
    la valida `verificar_propiedad()` en el servicio: DRF no conoce el partner
    hasta que se resuelve contra la base.
    """

    def has_permission(self, request, view) -> bool:
        return ROL_PARTNER_INTEGRACION in _roles(request)


class EsPartnerOGestor(BasePermission):
    """Lectura: el partner (lo suyo) o los gestores (cualquiera)."""

    def has_permission(self, request, view) -> bool:
        return bool(
            _roles(request)
            & {ROL_PARTNER_INTEGRACION, ROL_DESARROLLADOR_APIS, ROL_ADMINISTRADOR}
        )


class PropiedadPartnerError(Exception):
    """El actor no puede operar sobre ese partner. Se traduce a HTTP 403."""


def es_gestor(request) -> bool:
    """Administrador o Desarrollador de APIs: operan sobre cualquier partner.

    El Director Tecnológico **no** está aquí: es autoridad de los listados
    (FR-014a), no de la consola operativa. Ver `es_gestor_informes`.
    """
    return bool(_roles(request) & {ROL_ADMINISTRADOR, ROL_DESARROLLADOR_APIS})


def es_gestor_informes(request) -> bool:
    """Quien ve los cinco listados sin acotar: gestores operativos y el Director."""
    return bool(_roles(request) & ROLES_GESTORES_INFORMES)


class PartnerInexistenteError(Exception):
    """El partner del path no existe. Solo se traduce a 404 para un gestor."""


#: Cuerpo unico de denegacion para quien no es gestor. Que sea **el mismo texto**
#: en «no existe» y en «no es tuyo» es el requisito, no un descuido de redaccion.
DENEGACION_UNIFICADA = "El partner no pertenece al cliente autenticado"


def resolver_partner_visible(request, partner: dict[str, Any] | None) -> dict[str, Any]:
    """Devuelve el partner, o deniega sin revelar si existe.

    Por que existe esta funcion (PG-SEC-001, decisiones-pendientes #51): las
    vistas cortaban con `404 Partner no encontrado` antes de comprobar la
    propiedad, y solo despues devolvian `403` si el partner era ajeno. Para un
    Partner de integracion eso es un **oraculo de enumeracion**: iterando ids
    distingue «no existe» (404) de «existe y no es tuyo» (403), y con eso deduce
    cuantos partners hay y en que rangos — sin llegar a ver un solo dato.

    La separacion era deliberada y su razon era buena (`metricas_views.py`: «que
    el partner no exista no es un problema de permisos»). El conflicto real es
    claridad semantica contra no filtrar existencia, y se resuelve **segun quien
    pregunta**, no sacrificando uno de los dos:

    - **Gestor** (Administrador, Desarrollador de APIs): opera sobre cualquier
      partner, asi que un 404 no le revela nada que no pueda consultar. Conserva
      el diagnostico preciso.
    - **No gestor**: «no existe» y «no es tuyo» producen la **misma** respuesta,
      con el mismo cuerpo.

    Lanza `PartnerInexistenteError` (-> 404, solo gestores) o
    `PropiedadPartnerError` (-> 403).
    """
    if partner is None:
        if es_gestor(request):
            raise PartnerInexistenteError("Partner no encontrado")
        # Para el resto, un id inexistente se responde igual que uno ajeno.
        raise PropiedadPartnerError(DENEGACION_UNIFICADA)

    verificar_propiedad(request, partner)
    return partner


def verificar_propiedad(
    request,
    partner: dict[str, Any] | None,
    lookup: Any | None = None,
) -> None:
    """El partner del path debe pertenecer al cliente del token.

    Los gestores quedan exentos: su trabajo es operar sobre partners ajenos.
    Un Partner de integracion solo puede tocar el suyo.

    El token JWT lleva `idusuario` y `roles`, pero NO `idcliente`, asi que el
    cliente se resuelve con `ClienteLookupService` — el mismo que ya usa
    Soporte, en vez de duplicar la consulta.

    Lanza `PropiedadPartnerError` (-> 403); no devuelve booleano a proposito,
    para que sea imposible ignorar el resultado por descuido.
    """
    if partner is None:
        # Mismo texto que la denegacion por propiedad ajena, a proposito: las
        # vistas vuelcan `str(exc)` en `detail`, asi que un mensaje distinto
        # filtraria la existencia por el cuerpo aunque el codigo sea 403 en
        # ambos casos (PG-SEC-001). Para distinguirlos siendo gestor, usar
        # `resolver_partner_visible`.
        raise PropiedadPartnerError(DENEGACION_UNIFICADA)
    if es_gestor(request):
        return

    from apps.soporte_cliente.services.cliente_lookup_service import ClienteLookupService

    idusuario = getattr(getattr(request, "user", None), "idusuario", None)
    if idusuario is None:
        raise PropiedadPartnerError("Usuario no autenticado")

    idcliente_token = (lookup or ClienteLookupService()).resolve_idcliente(int(idusuario))
    if idcliente_token is None or int(partner.get("idcliente", -1)) != int(idcliente_token):
        raise PropiedadPartnerError(DENEGACION_UNIFICADA)


# ── Informes tacticos ────────────────────────────────────────────────────────
#
# Quien accede a los cinco listados, segun `acceso-tactico.md` §5. Aqui la
# autoridad departamental es unica —el **Director Tecnologico**, en los cinco—,
# a diferencia de Suscripciones y Red Operativa donde esta repartida.
#
# **No se reescribe el acotamiento.** `verificar_propiedad` ya resuelve la cuenta
# del solicitante con el mismo servicio que usa Soporte, exime a los gestores y
# **lanza en vez de devolver un booleano** — un `if not verificar(...)` olvidado
# seria un fallo silencioso de autorizacion. Los listados lo reutilizan tal cual.

#: Gestores operativos: incorporan, suspenden, emiten. **No** incluye al Director.
ROLES_GESTORES = frozenset({ROL_ADMINISTRADOR, ROL_DESARROLLADOR_APIS})

#: Lectura de los cinco listados sin acotar (FR-014a). El Director entra aquí
#: y **no** en `es_gestor()`: la consola operativa no se le abre por URL.
ROLES_GESTORES_INFORMES = frozenset(ROLES_GESTORES | {ROL_DIRECTOR_TECNOLOGICO})

#: Partners, credenciales y bitacora: gestores de informe **y** el propio partner.
ROLES_INFORMES_ACCESO = frozenset(ROLES_GESTORES_INFORMES | {ROL_PARTNER_INTEGRACION})

#: Versiones del contrato y alcance de datos: **solo** gestores de informe (FR-013).
#: El alcance de datos describe lo que cada CLIENTE tiene contratado, y las
#: versiones gobiernan el ciclo de vida del contrato: son materia de quien
#: administra la plataforma, no de quien la consume.
ROLES_INFORMES_CONTRATO = frozenset(ROLES_GESTORES_INFORMES)


class _RolesInformesPermission(BasePermission):
    """Base que falla cerrado: sin usuario, sin autenticar o sin rol, no pasa.

    Conceder aqui **no** implica ver todos los partners: el acotamiento lo
    resuelve `verificar_propiedad`, y a un partner lo fuerza al suyo.
    """

    roles_permitidos: frozenset[str] = frozenset()

    def has_permission(self, request, view) -> bool:
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return bool(set(getattr(user, "roles", []) or []) & self.roles_permitidos)


class InformesAccesoPermission(_RolesInformesPermission):
    """Partners, credenciales y cambios de acceso: gestores y partner."""

    roles_permitidos = ROLES_INFORMES_ACCESO


class InformesContratoPermission(_RolesInformesPermission):
    """Versiones del contrato y alcance de datos: solo gestores (FR-013)."""

    roles_permitidos = ROLES_INFORMES_CONTRATO
