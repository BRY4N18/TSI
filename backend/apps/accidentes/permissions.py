"""DRF permissions for accidentes module."""

from rest_framework.permissions import BasePermission

ROLE_TECNICO = "Tecnico"
ROLE_OPERADOR = "Operador"
ROLE_UNIDAD = "Unidad"
ROLE_ADMIN = "Administrador"

TECNICO_CAMPO_ROLES = frozenset({ROLE_TECNICO, ROLE_OPERADOR})


class OperadorEmergenciasPermission(BasePermission):
    """Allows Operador de emergencias (JWT role: Operador)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return ROLE_OPERADOR in getattr(user, "roles", [])


class AccidentesLecturaPermission(BasePermission):
    """Read-only access to accidentes (list/detail): Operador, Tecnico or Administrador."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return bool(roles & {ROLE_OPERADOR, ROLE_TECNICO, ROLE_ADMIN})


class UnidadEmergenciaPermission(BasePermission):
    """Allows Unidad de emergencia (JWT role: Unidad)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return ROLE_UNIDAD in getattr(user, "roles", [])


class IsTecnicoCampoOrUnidadOrAdmin(BasePermission):
    """Gallery read: Técnico/Operador, Unidad or Administrador (RN-EVI-012)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return bool(roles & TECNICO_CAMPO_ROLES) or ROLE_UNIDAD in roles or ROLE_ADMIN in roles


class IsTecnicoCampoOrUnidad(BasePermission):
    """Capture/write evidencia: Técnico/Operador or Unidad (not Administrador)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return bool(roles & TECNICO_CAMPO_ROLES) or ROLE_UNIDAD in roles
