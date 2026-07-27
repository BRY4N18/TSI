from rest_framework.permissions import BasePermission

CRM_ROLES = {"Administrador", "GerenteVentas", "GerenteCuentasPublicas"}
NOTIF_ROLES = {"Administrador", "GerenteVentas", "GerenteCuentasPublicas"}


class IsCRMUser(BasePermission):
    def has_permission(self, request, view):
        return bool(
            getattr(request.user, "is_authenticated", False)
            and CRM_ROLES.intersection(getattr(request.user, "roles", []) or [])
        )


class IsAdministradorCrm(BasePermission):
    def has_permission(self, request, view):
        roles = getattr(request.user, "roles", []) or []
        return bool(
            getattr(request.user, "is_authenticated", False) and "Administrador" in roles
        )


class IsGerenteOrAdminNotificaciones(BasePermission):
    def has_permission(self, request, view):
        return bool(
            getattr(request.user, "is_authenticated", False)
            and NOTIF_ROLES.intersection(getattr(request.user, "roles", []) or [])
        )
