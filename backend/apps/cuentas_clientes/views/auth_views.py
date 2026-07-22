"""Auth API views — login, logout, revoke-session."""

from __future__ import annotations

import logging

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.cuentas_clientes.services.auth_service import AuthenticationError, AuthService
from apps.cuentas_clientes.services.logout_service import LogoutError, LogoutService
from apps.cuentas_clientes.services.revoke_session_service import (
    ForbiddenRevokeError,
    RevokeSessionError,
    RevokeSessionService,
)
from core.api.response_envelope import error_response, success_response
from core.auth.permissions import IsAuthenticated401

logger = logging.getLogger("tsi.security.auth")


def _client_ip(request: Request) -> str | None:
    return request.META.get("REMOTE_ADDR")


class LoginView(APIView):
    authentication_classes = []  # No debe fallar por un token viejo/inválido en el cliente
    permission_classes = [AllowAny]

    def post(self, request: Request):
        gmail = request.data.get("gmail")
        password = request.data.get("password")

        if not gmail or not password:
            return error_response(
                "bad_request",
                "Campos invalidos",
                "400",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if len(password) < 8:
            return error_response(
                "bad_request",
                "Campos invalidos",
                "400",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        service = AuthService()
        try:
            data = service.login(
                gmail=gmail,
                password=password,
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                ip_address=_client_ip(request),
            )
        except AuthenticationError:
            return error_response(
                "unauthorized",
                "Token invalido o credenciales invalidas",
                "401",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        return success_response(data)


class LogoutView(APIView):
    authentication_classes = []  # Manual auth check for 401 contract compliance
    permission_classes = [AllowAny]

    def post(self, request: Request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return error_response(
                "unauthorized",
                "Token invalido o credenciales invalidas",
                "401",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        from apps.cuentas_clientes.authentication import JWTSessionAuthentication

        auth = JWTSessionAuthentication()
        try:
            user_auth = auth.authenticate(request)
        except Exception as exc:
            logger.debug("Fallo autenticación en revoke-session: %s", exc)
            return error_response(
                "unauthorized",
                "Token invalido o credenciales invalidas",
                "401",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        if not user_auth:
            return error_response(
                "unauthorized",
                "Token invalido o credenciales invalidas",
                "401",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        user, _token = user_auth
        service = LogoutService()
        try:
            data = service.logout(
                session_id=user.session_id,
                user_id=user.idusuario,
                ip_address=_client_ip(request),
            )
        except LogoutError:
            return error_response(
                "unauthorized",
                "Token invalido o credenciales invalidas",
                "401",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        return success_response(data)


class RevokeSessionView(APIView):
    permission_classes = [IsAuthenticated401]

    def post(self, request: Request):
        session_id = request.data.get("idsession")
        if session_id is None:
            return error_response(
                "bad_request",
                "Campos invalidos",
                "400",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user = request.user
        service = RevokeSessionService()
        try:
            data = service.revoke(
                session_id=int(session_id),
                admin_id=user.idusuario,
                admin_roles=user.roles,
                ip_address=_client_ip(request),
            )
        except ForbiddenRevokeError:
            return error_response(
                "forbidden",
                "Privilegios insuficientes",
                "403",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        except RevokeSessionError:
            return error_response(
                "bad_request",
                "Campos invalidos",
                "400",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        return success_response(data)
