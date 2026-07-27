"""DRF authentication for demo session Bearer tokens (typ=demo_session)."""
from __future__ import annotations

from types import SimpleNamespace

import jwt
from rest_framework import authentication, exceptions

from apps.ventas_crm.demo_tokens import decode_demo_session_token


class DemoSessionAuthentication(authentication.BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode("utf-8")
        if not header:
            return None
        parts = header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            return None
        token = parts[1]
        try:
            payload = decode_demo_session_token(token)
        except jwt.ExpiredSignatureError as exc:
            raise exceptions.AuthenticationFailed("demo session expirada") from exc
        except jwt.InvalidTokenError as exc:
            raise exceptions.AuthenticationFailed("demo session inválida") from exc
        if payload.get("typ") != "demo_session":
            raise exceptions.AuthenticationFailed("token no es demo_session")
        idprospecto = payload.get("idprospecto")
        if idprospecto is None:
            raise exceptions.AuthenticationFailed("demo session sin idprospecto")
        user = SimpleNamespace(
            is_authenticated=True,
            idprospecto=int(idprospecto),
            roles=["DemoProspecto"],
            is_demo_session=True,
        )
        return (user, token)
