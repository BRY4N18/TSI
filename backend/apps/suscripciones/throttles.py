"""DRF throttles — research Decision 11."""

from __future__ import annotations

from rest_framework.throttling import SimpleRateThrottle


class ProveedorBillingWriteThrottle(SimpleRateThrottle):
    scope = "suscripciones_proveedor_write"
    rate = "60/min"

    def get_cache_key(self, request, view):
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return None
        ident = getattr(user, "idusuario", None) or getattr(user, "pk", None)
        if ident is None:
            return None
        return self.cache_format % {"scope": self.scope, "ident": ident}


class AdminBillingThrottle(SimpleRateThrottle):
    scope = "suscripciones_admin"
    rate = "100/min"

    def get_cache_key(self, request, view):
        user = request.user
        if not user or not getattr(user, "is_authenticated", False):
            return None
        ident = getattr(user, "idusuario", None) or getattr(user, "pk", None)
        if ident is None:
            return None
        return self.cache_format % {"scope": self.scope, "ident": ident}
