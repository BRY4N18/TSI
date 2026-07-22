"""Onboarding API views — CU-O01, O12, O02, O09, O08."""

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cuentas_clientes.services.configuracion_cuenta_service import (
    ConfiguracionCuentaError,
    ConfiguracionCuentaService,
)
from apps.cuentas_clientes.services.invitacion_service import (
    InvitacionError,
    InvitacionService,
)
from apps.cuentas_clientes.services.logo_upload_service import (
    LogoUploadError,
    LogoUploadService,
)
from apps.cuentas_clientes.services.onboarding_access_service import (
    OnboardingAccessError,
)
from apps.cuentas_clientes.services.onboarding_service import (
    OnboardingError,
    OnboardingService,
)
from apps.cuentas_clientes.services.registro_cuenta_service import (
    RegistroCuentaError,
    RegistroCuentaService,
)
from apps.cuentas_clientes.views.cuenta_views import _client_ip, _require_auth
from core.api.response_envelope import error_response, success_response


class _OnboardingAuthenticatedView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]


class RegistrarCuentaView(_OnboardingAuthenticatedView):
    def post(self, request: Request):
        user, err = _require_auth(request)
        if err:
            return err
        service = RegistroCuentaService()
        try:
            data = service.registrar(
                user_id=user.idusuario,
                roles=user.roles,
                data=request.data,
                ip_address=_client_ip(request),
            )
        except OnboardingAccessError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        except RegistroCuentaError as exc:
            detail = str(exc)
            if "ya registrado" in detail.lower():
                return error_response("conflict", detail, "409", status_code=409)
            return error_response("bad_request", detail, "400", status_code=400)
        return success_response(data, status_code=status.HTTP_201_CREATED)


class ConfigurarCuentaView(_OnboardingAuthenticatedView):
    def patch(self, request: Request, idcliente: int):
        user, err = _require_auth(request)
        if err:
            return err
        service = ConfiguracionCuentaService()
        try:
            data = service.configurar(
                user_id=user.idusuario,
                roles=user.roles,
                cliente_id=idcliente,
                data=request.data,
                ip_address=_client_ip(request),
            )
        except OnboardingAccessError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        except ConfiguracionCuentaError as exc:
            detail = str(exc)
            if "no encontrada" in detail:
                return error_response("not_found", detail, "404", status_code=404)
            if "completado" in detail.lower():
                return error_response("conflict", detail, "409", status_code=409)
            return error_response("bad_request", detail, "400", status_code=400)
        return success_response(data)


class OnboardingLogoUploadUrlView(_OnboardingAuthenticatedView):
    def post(self, request: Request, idcliente: int):
        user, err = _require_auth(request)
        if err:
            return err
        content_type = request.data.get("content_type")
        if not content_type:
            return error_response("bad_request", "Campos invalidos", "400", status_code=400)

        from apps.cuentas_clientes.services.onboarding_access_service import (
            OnboardingAccessService,
        )

        access = OnboardingAccessService()
        try:
            access.require_admin_global(user.roles)
        except OnboardingAccessError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)

        service = LogoUploadService()
        try:
            data = service.create_upload_url(
                user_id=user.idusuario,
                roles=user.roles,
                cliente_id=idcliente,
                content_type=content_type,
                file_name=request.data.get("file_name"),
            )
        except LogoUploadError as exc:
            detail = str(exc)
            if "no encontrada" in detail:
                return error_response("not_found", detail, "404", status_code=404)
            return error_response("bad_request", detail, "400", status_code=400)
        return success_response(data)


class OnboardingProgresoView(_OnboardingAuthenticatedView):
    def get(self, request: Request, idcliente: int):
        user, err = _require_auth(request)
        if err:
            return err
        service = OnboardingService()
        try:
            data = service.get_progreso(
                user_id=user.idusuario,
                roles=user.roles,
                cliente_id=idcliente,
            )
        except OnboardingAccessError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        except OnboardingError as exc:
            detail = str(exc)
            if "no encontrada" in detail:
                return error_response("not_found", detail, "404", status_code=404)
            return error_response("bad_request", detail, "400", status_code=400)
        return success_response(data)


class CompletarOnboardingEtapaView(_OnboardingAuthenticatedView):
    def post(self, request: Request, idcliente: int):
        user, err = _require_auth(request)
        if err:
            return err
        etapa = request.data.get("etapa")
        if not etapa:
            return error_response("bad_request", "etapa requerida", "400", status_code=400)

        service = OnboardingService()
        try:
            data = service.completar_etapa(
                user_id=user.idusuario,
                roles=user.roles,
                cliente_id=idcliente,
                etapa=etapa,
                datos_etapa=request.data.get("datos_etapa"),
                ip_address=_client_ip(request),
            )
        except OnboardingAccessError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        except OnboardingError as exc:
            detail = str(exc)
            if "no encontrada" in detail:
                return error_response("not_found", detail, "404", status_code=404)
            if "ya completada" in detail.lower() or "completado" in detail.lower():
                return error_response("conflict", detail, "409", status_code=409)
            return error_response("bad_request", detail, "400", status_code=400)
        return success_response(data)


class ReenviarInvitacionView(_OnboardingAuthenticatedView):
    def post(self, request: Request, idcliente: int):
        user, err = _require_auth(request)
        if err:
            return err
        target = request.data.get("id_usuario") if request.data else None
        service = InvitacionService()
        try:
            data = service.reenviar(
                user_id=user.idusuario,
                roles=user.roles,
                cliente_id=idcliente,
                target_user_id=int(target) if target is not None else None,
                ip_address=_client_ip(request),
            )
        except OnboardingAccessError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        except InvitacionError as exc:
            detail = str(exc)
            if "no encontrada" in detail or "no encontrado" in detail:
                return error_response("not_found", detail, "404", status_code=404)
            if "no pertenece" in detail:
                return error_response("forbidden", detail, "403", status_code=403)
            return error_response("bad_request", detail, "400", status_code=400)
        return success_response(data)
