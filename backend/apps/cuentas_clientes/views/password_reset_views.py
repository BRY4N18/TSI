"""Password reset API view."""

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.cuentas_clientes.services.password_reset_service import (
    PasswordResetError,
    PasswordResetService,
)
from apps.cuentas_clientes.views.error_response import error_response, success_response


class PasswordResetView(APIView):
    authentication_classes = []  # No debe fallar por un token viejo/inválido en el cliente
    permission_classes = [AllowAny]

    def post(self, request: Request):
        gmail = request.data.get("gmail")
        if not gmail:
            return error_response(
                "bad_request",
                "Campos invalidos",
                "400",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        service = PasswordResetService()
        try:
            data = service.request_reset(
                gmail=gmail,
                ip_address=request.META.get("REMOTE_ADDR"),
            )
        except PasswordResetError:
            return error_response(
                "unauthorized",
                "Token invalido o credenciales invalidas",
                "401",
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        return success_response(data)
