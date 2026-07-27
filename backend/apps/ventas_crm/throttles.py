from rest_framework.throttling import AnonRateThrottle, SimpleRateThrottle


class ProspectoRegistroThrottle(AnonRateThrottle):
    scope = "prospecto_registro"


class DemoSesionIpThrottle(AnonRateThrottle):
    scope = "demo_sesion_ip"


class DemoInteraccionTokenThrottle(SimpleRateThrottle):
    scope = "demo_interaccion_token"

    def get_cache_key(self, request, view):
        auth = getattr(request, "auth", None)
        if not auth:
            return None
        return self.cache_format % {
            "scope": self.scope,
            "ident": str(auth)[:64],
        }
