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
        return ROL_SOPORTE in roles or ROL_ADMINISTRADOR in roles


class IsNivelEscaladoSoporte(BasePermission):
    """Desarrollador de APIs o Director Tecnológico — nivel de escalado."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return (
            ROL_DESARROLLADOR_APIS in roles
            or ROL_DIRECTOR_TECNOLOGICO in roles
            or ROL_ADMINISTRADOR in roles
        )


class IsSoporteAgenteOrNivelEscalado(BasePermission):
    """Soporte al cliente, Desarrollador de APIs o Director Tecnológico — resuelve tickets
    (incluye los ya escalados, ver transición Escalado -> Resuelto)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return bool(
            roles
            & {ROL_SOPORTE, ROL_ADMINISTRADOR, ROL_DESARROLLADOR_APIS, ROL_DIRECTOR_TECNOLOGICO}
        )


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
        return bool(
            roles
            & (
                ROLES_REPORTADORES
                | {
                    ROL_SOPORTE,
                    ROL_ADMINISTRADOR,
                    ROL_DESARROLLADOR_APIS,
                    ROL_DIRECTOR_TECNOLOGICO,
                }
            )
        )


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
