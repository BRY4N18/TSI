"""DRF permissions for disponibilidad de unidad."""

from __future__ import annotations

from rest_framework.permissions import BasePermission

from core.repositories.despacho.unidad_emergencia_repository import UnidadEmergenciaRepository

ROLE_UNIDAD = "Unidad"
ROLE_ADMIN = "Administrador"
ROLE_DESPACHO = "Despacho"
ROLE_OPERADOR = "Operador"
ROLE_DIRECTOR_TECNOLOGICO = "DirectorTecnologico"


class IsUnidadDespachoOwn(BasePermission):
    """Allows Unidad role with linked emergency unit for /mi-despacho/* endpoints."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        if ROLE_UNIDAD not in getattr(user, "roles", []):
            return False
        return UnidadEmergenciaRepository().find_by_usuario(user.idusuario) is not None


class IsOperadorDespacho(BasePermission):
    """Operador or Despacho service role for assignment/monitoring endpoints."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return ROLE_OPERADOR in roles or ROLE_DESPACHO in roles or ROLE_ADMIN in roles


class IsDirectorTecnologicoOrAdmin(BasePermission):
    """Director Tecnológico or Administrador for RF-DES-010 parameters."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return ROLE_DIRECTOR_TECNOLOGICO in roles or ROLE_ADMIN in roles


class IsUnidadEmergenciaOwn(BasePermission):
    """Allows only Unidad role for /mi-unidad-emergencia/* endpoints."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        if ROLE_UNIDAD not in getattr(user, "roles", []):
            return False
        return UnidadEmergenciaRepository().find_by_usuario(user.idusuario) is not None


class IsAdministradorOrDespachoService(BasePermission):
    """Allows Administrador or Despacho service role for fleet listing."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return ROLE_ADMIN in roles or ROLE_DESPACHO in roles


class IsUnidadEmergenciaSelfOrAdmin(BasePermission):
    """Unidad sees own unit; Administrador/Despacho see any unit."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        if ROLE_ADMIN in roles or ROLE_DESPACHO in roles:
            return True
        if ROLE_UNIDAD in roles:
            unit_id = view.kwargs.get("idunidademergencia")
            if unit_id is None:
                return True
            own = UnidadEmergenciaRepository().find_by_usuario(user.idusuario)
            return own is not None and own["idunidademergencia"] == int(unit_id)
        return False
