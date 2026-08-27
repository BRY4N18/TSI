"""DRF permissions for gestión de tickets de soporte."""

from __future__ import annotations

from rest_framework.permissions import BasePermission

from apps.partners.domain_constants import ROL_PARTNER_INTEGRACION
from apps.soporte_cliente.domain_constants import (
    ROL_ADMINISTRADOR,
    ROL_CLIENTE,
    ROL_DESARROLLADOR_APIS,
    ROL_DIRECTOR_TECNOLOGICO,
    ROL_SOPORTE,
)


# Quien REPORTA un ticket. `PartnerIntegracion` esta aqui porque el SRS dice que
# el partner puede registrar una disputa sobre su factura: es el mismo actor
# —quien recibe el servicio y reclama—, solo que su relacion con TSI pasa por la
# API en vez de por el portal. Excluirlo dejaba la disputa de facturacion sin
# nadie que pudiera abrirla desde el lado del partner (era el hallazgo F18).
ROLES_REPORTADORES = frozenset({ROL_CLIENTE, ROL_PARTNER_INTEGRACION})


# ⚠️ **`Administrador` NO atiende tickets** (revisión 24/08/2026, hallazgo #18).
#
# Hasta 2026-08-26 todos los permisos de este módulo incluían `ROL_ADMINISTRADOR`,
# así que la gestión de tickets —tomar, comentar, escalar, resolver, y la cola
# entera con sus notas internas— quedaba abierta a quien administra la
# plataforma. La revisora lo señaló al revés de como suele aparecer un bug de
# permisos: no es que a alguien le falte acceso, es que le sobra.
#
# Administrar la plataforma y atender a un cliente son dos trabajos distintos.
# El Administrador conserva lo que sí es suyo —configurar el SLA
# (`IsAdministradorSLA`, CU-O97)—; la cola es del equipo de soporte.
ROLES_AGENTE = frozenset({ROL_SOPORTE})
ROLES_NIVEL_ESCALADO = frozenset({ROL_DESARROLLADOR_APIS, ROL_DIRECTOR_TECNOLOGICO})


class IsClienteSoporte(BasePermission):
    """Reportador del ticket (Cliente o PartnerIntegracion) — registra, comenta,
    confirma cierre, reabre. La pertenencia del ticket la sigue filtrando cada
    vista por `idcliente`: este permiso solo abre la puerta, no da alcance."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return bool(ROLES_REPORTADORES & set(getattr(user, "roles", [])))


class IsSoporteAgente(BasePermission):
    """Soporte al cliente (agente) — toma, comenta, escala, resuelve."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return bool(ROLES_AGENTE & roles)


class IsNivelEscaladoSoporte(BasePermission):
    """Desarrollador de APIs o Director Tecnológico — nivel de escalado."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return bool(ROLES_NIVEL_ESCALADO & roles)


class IsSoporteAgenteOrNivelEscalado(BasePermission):
    """Soporte al cliente, Desarrollador de APIs o Director Tecnológico — resuelve tickets
    (incluye los ya escalados, ver transición Escalado -> Resuelto)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return bool(roles & (ROLES_AGENTE | ROLES_NIVEL_ESCALADO))


class IsAdministradorSLA(BasePermission):
    """Administrador — configura Dim_SLAConfig (CU-O97)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return ROL_ADMINISTRADOR in getattr(user, "roles", [])


class IsSoporteAgenteOrCliente(BasePermission):
    """Lectura/listado accesible al reportador (sus tickets) y agentes/admin (todos)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return bool(roles & (ROLES_REPORTADORES | ROLES_AGENTE | ROLES_NIVEL_ESCALADO))


def es_solo_reportador(roles) -> bool:
    """True si el usuario SOLO reporta —Cliente o PartnerIntegracion— y por tanto
    su vista debe acotarse a sus propios tickets y ocultar las notas internas.

    Existe como funcion y no como comparacion suelta porque las vistas lo hacian
    con `roles == {ROL_CLIENTE}`: al admitir al partner (F18), esa igualdad lo
    habria dejado **fuera del acotamiento**, es decir viendo tickets ajenos y
    notas internas. El acotamiento no se decide por "ser Cliente" sino por "no
    tener ningun rol de atencion".
    """
    return bool(roles) and set(roles) <= ROLES_REPORTADORES


# ── Informes tácticos simples (OT19, OT20) ───────────────────────────────────
#
# ⚠️ El acotamiento NO se declara aquí, sino en el resolutor transversal. Este
# permiso solo abre la puerta; quién ve qué lo decide `resolver_organizacion`.

from core.auth.roles_tacticos import ROL_GERENTE_EXITO_CLIENTE  # noqa: E402

#: Quien ATIENDE tickets. Tener **alguno** de estos saca del acotamiento.
#:
#: `GerenteExitoCliente` es la autoridad del departamento (acceso-tactico §5).
#: **No es `SupervisorSoporte`**: ese es el destinatario operativo de un escalado
#: automático, no la autoridad. Conviven y sus permisos son independientes.
#: `Administrador` tampoco está aquí: ver la nota de `ROLES_AGENTE`. Los informes
#: de soporte son la lectura del trabajo de este equipo, no un tablero de
#: administración de la plataforma.
ROLES_ATENCION = frozenset(
    ROLES_AGENTE | ROLES_NIVEL_ESCALADO | {ROL_GERENTE_EXITO_CLIENTE}
)

#: Tickets: atienden y reportan. Escalados: **solo atienden** (FR-008).
ROLES_INFORMES_TICKETS = frozenset(ROLES_ATENCION | ROLES_REPORTADORES)
ROLES_INFORMES_ESCALADOS = frozenset(ROLES_ATENCION)


class _RolesInformesPermission(BasePermission):
    """Base que falla cerrado: sin usuario, sin autenticar o sin rol, no pasa."""

    roles_permitidos: frozenset = frozenset()

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return bool(self.roles_permitidos & set(getattr(user, "roles", []) or []))


class InformesTicketsPermission(_RolesInformesPermission):
    """Cola de tickets: la ve quien atiende y quien reporta.

    Conceder aquí **no** implica ver todos los tickets: un reportador entra y
    queda acotado a su cuenta. Son dos comprobaciones distintas y sucesivas.
    """

    roles_permitidos = ROLES_INFORMES_TICKETS


class InformesEscaladosPermission(_RolesInformesPermission):
    """Escalados: **solo roles de atención** (FR-008).

    Un escalado es proceso interno del equipo de soporte, no información que el
    reportador necesite sobre su propio ticket.
    """

    roles_permitidos = ROLES_INFORMES_ESCALADOS
