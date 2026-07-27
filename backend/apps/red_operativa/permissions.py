"""DRF permissions for red_operativa (alta-unidades + incorporacion-regional)."""

from __future__ import annotations

from rest_framework.permissions import BasePermission

from apps.red_operativa.services.proveedor_access_service import (
    ProveedorAccessError,
    ProveedorAccessService,
)

ROLE_ADMIN = "Administrador"
ROLE_OPERADOR = "Operador"
ROLE_DIRECTOR_TECNOLOGICO = "DirectorTecnologico"
ROLE_CLIENTE = "Cliente"
ROLE_PROVEEDOR = "Proveedor"


class IsProveedorFlota(BasePermission):
    """CU-O54/56/57/58 — solo Proveedor (admin_local de cuenta Activo). Sin override Admin."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = list(getattr(user, "roles", []) or [])
        if ROLE_CLIENTE not in roles and ROLE_PROVEEDOR not in roles:
            return False
        try:
            cliente = ProveedorAccessService().resolve_cliente_activo(
                user_id=user.idusuario, roles=roles
            )
        except ProveedorAccessError:
            return False
        request.proveedor_idcliente = cliente["idcliente"]
        return True


class IsAdministradorRedOperativa(BasePermission):
    """Deprecated for unit CRUD — kept for regional admin endpoints if referenced."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return ROLE_ADMIN in getattr(user, "roles", [])


class IsAdministradorOrOperador(BasePermission):
    """Legacy read helper — unit detail now uses IsProveedorFlota."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return ROLE_ADMIN in roles or ROLE_OPERADOR in roles


class IsDirectorTecnologico(BasePermission):
    """Exclusivo para CU-O61 (re-evaluar/despublicar región en producción)."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return ROLE_DIRECTOR_TECNOLOGICO in getattr(user, "roles", [])


class IsAdministradorOrDirectorTecnologico(BasePermission):
    """Ejecutar/consultar CU-O55/O60."""

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        roles = set(getattr(user, "roles", []))
        return ROLE_ADMIN in roles or ROLE_DIRECTOR_TECNOLOGICO in roles
