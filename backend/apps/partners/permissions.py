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
    """Administrador o Desarrollador de APIs: operan sobre cualquier partner."""
    return bool(_roles(request) & {ROL_ADMINISTRADOR, ROL_DESARROLLADOR_APIS})


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
        raise PropiedadPartnerError("Partner no encontrado")
    if es_gestor(request):
        return

    from apps.soporte_cliente.services.cliente_lookup_service import ClienteLookupService

    idusuario = getattr(getattr(request, "user", None), "idusuario", None)
    if idusuario is None:
        raise PropiedadPartnerError("Usuario no autenticado")

    idcliente_token = (lookup or ClienteLookupService()).resolve_idcliente(int(idusuario))
    if idcliente_token is None or int(partner.get("idcliente", -1)) != int(idcliente_token):
        raise PropiedadPartnerError("El partner no pertenece al cliente autenticado")


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

#: Gestores: operan sobre cualquier partner.
ROLES_GESTORES = frozenset({ROL_ADMINISTRADOR, ROL_DESARROLLADOR_APIS})

#: Partners, credenciales y bitacora: gestores **y** el propio partner.
ROLES_INFORMES_ACCESO = frozenset(ROLES_GESTORES | {ROL_PARTNER_INTEGRACION})

#: Versiones del contrato y alcance de datos: **solo gestores** (FR-013).
#: El alcance de datos describe lo que cada CLIENTE tiene contratado, y las
#: versiones gobiernan el ciclo de vida del contrato: son materia de quien
#: administra la plataforma, no de quien la consume.
ROLES_INFORMES_CONTRATO = frozenset(ROLES_GESTORES)


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
