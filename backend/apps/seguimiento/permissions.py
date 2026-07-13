"""DRF permissions for seguimiento module."""

from __future__ import annotations

from rest_framework.permissions import BasePermission

from core.repositories.despacho.unidad_emergencia_repository import UnidadEmergenciaRepository

ROLE_UNIDAD = "Unidad"
ROLE_ADMIN = "Administrador"
ROLE_DESPACHO = "Despacho"
ROLE_OPERADOR = "Operador"
ROLE_CLIENTE = "Cliente"


class IsUnidadSeguimiento(BasePermission):
    """Unidad role with linked emergency unit for /mi-seguimiento/*."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        if ROLE_UNIDAD not in getattr(user, "roles", []):
            return False
        return UnidadEmergenciaRepository().find_by_usuario(user.idusuario) is not None


class IsOperadorSeguimiento(BasePermission):
    """Operador or Despacho for mapa, historial and cierre operador."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return ROLE_OPERADOR in roles or ROLE_DESPACHO in roles or ROLE_ADMIN in roles


class IsClienteExpediente(BasePermission):
    """Cliente role for expedientes cerrados (no mapa activo)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return ROLE_CLIENTE in getattr(user, "roles", [])
