"""Password reset API views — solicitud de temporal (CU-O03) y cambio definitivo (CU-O04)."""

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.cuentas_clientes.services.cambio_password_service import (
    CambioPasswordError,
    CambioPasswordService,
)
from apps.cuentas_clientes.services.password_reset_service import (
    PasswordResetError,
    PasswordResetService,
)
from core.api.response_envelope import error_response, success_response
from core.auth.permissions import IsAuthenticated401

_ESTADOS_HTTP = {
    "unauthorized": status.HTTP_401_UNAUTHORIZED,
    "not_found": status.HTTP_404_NOT_FOUND,
    "validation_error": status.HTTP_400_BAD_REQUEST,
}


class PasswordChangeView(APIView):
    """Define la contraseña definitiva del usuario autenticado (CU-O04).

    Requiere sesión: es el paso que desbloquea al usuario que entró con una
    credencial temporal, y hasta ahora no existía — el login forzaba el cambio y
    la única pantalla disponible se limitaba a enviar otra temporal.
    """

    permission_classes = [IsAuthenticated401]

    def post(self, request: Request):
        actual = request.data.get("password_actual")
        nueva = request.data.get("password_nueva")
        if not actual or not nueva:
            return error_response(
                "bad_request", "Campos invalidos", "400", status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            data = CambioPasswordService().cambiar(
                user_id=request.user.idusuario,
                password_actual=actual,
                password_nueva=nueva,
                ip_address=request.META.get("REMOTE_ADDR"),
            )
        except CambioPasswordError as exc:
            codigo = _ESTADOS_HTTP.get(exc.code, status.HTTP_400_BAD_REQUEST)
            return error_response(exc.code, exc.detail, str(codigo), status_code=codigo)

        return success_response(data)


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
