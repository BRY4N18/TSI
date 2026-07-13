"""Cuenta de cliente API views — CU-O03, CU-O10, CU-O11."""

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cuentas_clientes.authentication import AuthenticatedUser, JWTSessionAuthentication
from apps.cuentas_clientes.services.baja_cuenta_service import BajaCuentaError, BajaCuentaService
from apps.cuentas_clientes.services.cuenta_access_service import CuentaAccessError
from apps.cuentas_clientes.services.cuenta_perfil_service import CuentaPerfilError, CuentaPerfilService
from apps.cuentas_clientes.services.cuenta_preferencias_service import (
    CuentaPreferenciasError,
    CuentaPreferenciasService,
)
from apps.cuentas_clientes.services.logo_upload_service import LogoUploadError, LogoUploadService
from apps.cuentas_clientes.services.transferencia_propiedad_service import (
    TransferenciaPropiedadError,
    TransferenciaPropiedadService,
)
from apps.cuentas_clientes.views.error_response import error_response, success_response


def _client_ip(request: Request) -> str | None:
    return request.META.get("REMOTE_ADDR")


def _require_auth(request: Request) -> tuple[AuthenticatedUser | None, Response | None]:
    """Manual JWT check for 401 contract compliance (matches LogoutView pattern)."""
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Bearer "):
        return None, error_response(
            "unauthorized",
            "Credenciales de autenticación no provistas.",
            "401",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        result = JWTSessionAuthentication().authenticate(request)
    except Exception:
        return None, error_response(
            "unauthorized",
            "Token invalido o credenciales invalidas",
            "401",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if not result:
        return None, error_response(
            "unauthorized",
            "Credenciales de autenticación no provistas.",
            "401",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    return result[0], None


class _CuentaAuthenticatedView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]


class CuentaPerfilView(_CuentaAuthenticatedView):
    def get(self, request: Request, idcliente: int):
        user, err = _require_auth(request)
        if err:
            return err
        service = CuentaPerfilService()
        try:
            data = service.get_perfil(
                user_id=user.idusuario,
                roles=user.roles,
                cliente_id=idcliente,
            )
        except CuentaAccessError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        except CuentaPerfilError:
            return error_response("not_found", "Cuenta de cliente no encontrada", "404", status_code=404)
        return success_response(data)

    def patch(self, request: Request, idcliente: int):
        user, err = _require_auth(request)
        if err:
            return err
        service = CuentaPerfilService()
        try:
            data = service.update_perfil(
                user_id=user.idusuario,
                roles=user.roles,
                cliente_id=idcliente,
                data=request.data,
                ip_address=_client_ip(request),
            )
        except CuentaAccessError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        except CuentaPerfilError as exc:
            detail = str(exc)
            if "no encontrada" in detail:
                return error_response("not_found", detail, "404", status_code=404)
            if "baja" in detail.lower():
                return error_response("conflict", detail, "409", status_code=409)
            return error_response("bad_request", detail, "400", status_code=400)
        return success_response(data)


class CuentaPreferenciasView(_CuentaAuthenticatedView):
    def get(self, request: Request, idcliente: int):
        user, err = _require_auth(request)
        if err:
            return err
        service = CuentaPreferenciasService()
        try:
            data = service.get_preferencias(
                user_id=user.idusuario,
                roles=user.roles,
                cliente_id=idcliente,
            )
        except CuentaAccessError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        except CuentaPreferenciasError:
            return error_response("not_found", "Preferencias no encontradas", "404", status_code=404)
        return success_response(data)

    def patch(self, request: Request, idcliente: int):
        user, err = _require_auth(request)
        if err:
            return err
        service = CuentaPreferenciasService()
        try:
            data = service.update_preferencias(
                user_id=user.idusuario,
                roles=user.roles,
                cliente_id=idcliente,
                data=request.data,
                ip_address=_client_ip(request),
            )
        except CuentaAccessError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        except CuentaPreferenciasError as exc:
            detail = str(exc)
            if "no encontrad" in detail:
                return error_response("not_found", detail, "404", status_code=404)
            if "baja" in detail.lower():
                return error_response("conflict", detail, "409", status_code=409)
            return error_response("bad_request", detail, "400", status_code=400)
        return success_response(data)


class LogoUploadUrlView(_CuentaAuthenticatedView):
    def post(self, request: Request, idcliente: int):
        user, err = _require_auth(request)
        if err:
            return err
        content_type = request.data.get("content_type")
        if not content_type:
            return error_response("bad_request", "Campos invalidos", "400", status_code=400)

        service = LogoUploadService()
        try:
            data = service.create_upload_url(
                user_id=user.idusuario,
                roles=user.roles,
                cliente_id=idcliente,
                content_type=content_type,
                file_name=request.data.get("file_name"),
            )
        except CuentaAccessError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        except LogoUploadError as exc:
            detail = str(exc)
            if "no encontrada" in detail or "baja" in detail.lower():
                code = 409 if "baja" in detail.lower() else 404
                err_name = "conflict" if code == 409 else "not_found"
                return error_response(err_name, detail, str(code), status_code=code)
            return error_response("bad_request", detail, "400", status_code=400)
        return success_response(data)


class UsuariosElegiblesView(_CuentaAuthenticatedView):
    def get(self, request: Request, idcliente: int):
        user, err = _require_auth(request)
        if err:
            return err
        service = TransferenciaPropiedadService()
        try:
            usuarios = service.list_usuarios_elegibles(
                user_id=user.idusuario,
                roles=user.roles,
                cliente_id=idcliente,
            )
        except CuentaAccessError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        except TransferenciaPropiedadError:
            return error_response("not_found", "Cuenta de cliente no encontrada", "404", status_code=404)
        return success_response({"usuarios": usuarios})


class TransferenciaPropiedadView(_CuentaAuthenticatedView):
    def post(self, request: Request, idcliente: int):
        user, err = _require_auth(request)
        if err:
            return err
        nuevo_id = request.data.get("id_nuevo_responsable")
        if not nuevo_id:
            return error_response("bad_request", "Campos invalidos", "400", status_code=400)

        service = TransferenciaPropiedadService()
        try:
            data = service.transferir(
                user_id=user.idusuario,
                roles=user.roles,
                cliente_id=idcliente,
                nuevo_responsable_id=int(nuevo_id),
                ip_address=_client_ip(request),
            )
        except CuentaAccessError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        except TransferenciaPropiedadError as exc:
            detail = str(exc)
            if "no encontrada" in detail or "no pertenece" in detail:
                return error_response("not_found", detail, "404", status_code=404)
            if "baja" in detail.lower() or "ya es admin" in detail:
                return error_response("conflict", detail, "409", status_code=409)
            return error_response("bad_request", detail, "400", status_code=400)
        return success_response(data)


class BajaCuentaView(_CuentaAuthenticatedView):
    def post(self, request: Request, idcliente: int):
        user, err = _require_auth(request)
        if err:
            return err
        service = BajaCuentaService()
        try:
            data = service.dar_baja(
                user_id=user.idusuario,
                roles=user.roles,
                cliente_id=idcliente,
                motivo=request.data.get("motivo"),
                ip_address=_client_ip(request),
            )
        except CuentaAccessError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        except BajaCuentaError as exc:
            detail = str(exc)
            if "no encontrada" in detail:
                return error_response("not_found", detail, "404", status_code=404)
            return error_response("conflict", detail, "409", status_code=409)
        return success_response(data)
