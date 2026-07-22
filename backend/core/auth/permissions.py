"""Custom DRF permissions returning 401 for unauthenticated requests."""

from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import IsAuthenticated


class IsAuthenticated401(IsAuthenticated):
    """Raise 401 NotAuthenticated instead of 403 when no credentials."""

    def has_permission(self, request, view):
        if not request.user or not getattr(request.user, "is_authenticated", False):
            raise NotAuthenticated("Credenciales de autenticación no provistas.")
        return True
