"""DRF authentication: JWT RS256 + session validation."""

from __future__ import annotations

from dataclasses import dataclass

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from apps.cuentas_clientes.services.session_validation_service import (
    SessionValidationService,
)
from core.seguridad.cadena_critica import es_cadena_critica


@dataclass
class AuthenticatedUser:
    idusuario: int
    roles: list[str]
    session_id: int

    @property
    def is_authenticated(self) -> bool:
        return True


class JWTSessionAuthentication(BaseAuthentication):
    """Validate Bearer JWT and active session on every protected request."""

    keyword = "Bearer"

    def authenticate_header(self, request):
        return self.keyword

    def __init__(self):
        self.session_validator = SessionValidationService()

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith(f"{self.keyword} "):
            return None

        token = auth_header[len(self.keyword) + 1 :].strip()
        if not token:
            return None

        # La cadena critica se resuelve **aqui** y no en el servicio porque este
        # es el unico punto que conoce la ruta. El servicio recibe una decision
        # ya tomada, en vez de importar el enrutador para inspeccionarla.
        degradable = es_cadena_critica(getattr(request, "path", ""))

        try:
            claims = self.session_validator.validate_token_and_session(
                token, degradable=degradable
            )
        except Exception as exc:
            raise AuthenticationFailed("Token invalido o credenciales invalidas") from exc

        user = AuthenticatedUser(
            idusuario=int(claims["sub"]),
            roles=claims.get("roles", []),
            session_id=int(claims["session_id"]),
        )
        return (user, token)
