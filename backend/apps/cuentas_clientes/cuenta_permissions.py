"""DRF permission helpers for cuenta de cliente — delegates to CuentaAccessService."""

from __future__ import annotations

from rest_framework.permissions import BasePermission

from apps.cuentas_clientes.authentication import AuthenticatedUser
from apps.cuentas_clientes.services.cuenta_access_service import CuentaAccessService


class IsCuentaAccessible(BasePermission):
    """User can access the idcliente in view kwargs."""

    def has_permission(self, request, view) -> bool:
        user: AuthenticatedUser = request.user
        cliente_id = view.kwargs.get("idcliente")
        if not cliente_id:
            return False
        service = CuentaAccessService()
        return service.can_access_cuenta(
            user_id=user.idusuario,
            roles=user.roles,
            cliente_id=int(cliente_id),
        )


class IsAdminLocal(BasePermission):
    """User is admin_local_id for the cuenta."""

    def has_permission(self, request, view) -> bool:
        user: AuthenticatedUser = request.user
        cliente_id = view.kwargs.get("idcliente")
        if not cliente_id:
            return False
        service = CuentaAccessService()
        return service.is_admin_local(user_id=user.idusuario, cliente_id=int(cliente_id))
