"""DRF permissions — Proveedor / Administrador billing."""

from __future__ import annotations

from rest_framework.permissions import BasePermission

from apps.red_operativa.services.proveedor_access_service import (
    ProveedorAccessError,
    ProveedorAccessService,
)

ROLE_ADMIN = "Administrador"
ROLE_CLIENTE = "Cliente"
ROLE_PROVEEDOR = "Proveedor"


class IsProveedorCuenta(BasePermission):
    """Proveedor/Cliente admin_local de cuenta Activo — setea request.billing_idcliente."""

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
        request.billing_idcliente = cliente["idcliente"]
        return True


class IsAdministradorBilling(BasePermission):
    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return ROLE_ADMIN in getattr(user, "roles", [])


class IsProveedorOrAdminBilling(BasePermission):
    def has_permission(self, request, view) -> bool:
        if IsAdministradorBilling().has_permission(request, view):
            return True
        return IsProveedorCuenta().has_permission(request, view)
