"""Onboarding API views — CU-O14, O16; O01/O12 retirados (410)."""

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.cuentas_clientes.services.aprobacion_proveedor_service import (
    AprobacionProveedorError,
    AprobacionProveedorService,
)
from apps.cuentas_clientes.services.autorregistro_proveedor_service import (
    AutorregistroProveedorError,
    AutorregistroProveedorService,
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
    OnboardingAccessService,
)
from apps.cuentas_clientes.services.onboarding_service import (
    OnboardingError,
    OnboardingService,
)
from apps.cuentas_clientes.views.cuenta_views import _client_ip, _require_auth
from core.api.response_envelope import error_response, success_response


class _OnboardingAuthenticatedView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]


class AutorregistroProveedorView(_OnboardingAuthenticatedView):
    """CU-O14 — public self-registration."""

    def post(self, request: Request):
        service = AutorregistroProveedorService()
        try:
            data = service.autorregistrar(
                data=request.data,
                ip_address=_client_ip(request),
            )
        except AutorregistroProveedorError as exc:
            detail = str(exc)
            if "ya registrado" in detail.lower():
                return error_response("conflict", detail, "409", status_code=409)
            return error_response("bad_request", detail, "400", status_code=400)
        return success_response(data, status_code=status.HTTP_201_CREATED)


class ListarSolicitudesProveedorView(_OnboardingAuthenticatedView):
    def get(self, request: Request):
        user, err = _require_auth(request)
        if err:
            return err
        estado = request.query_params.get("estado", "Pendiente_Aprobación")
        service = AprobacionProveedorService()
        try:
            data = service.listar_solicitudes(roles=user.roles, estado=estado)
        except OnboardingAccessError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        except AprobacionProveedorError as exc:
            return error_response("bad_request", str(exc), "400", status_code=400)
        return success_response(data)


class DecidirSolicitudProveedorView(_OnboardingAuthenticatedView):
    def post(self, request: Request, idcliente: int):
        user, err = _require_auth(request)
        if err:
            return err
        service = AprobacionProveedorService()
        try:
            data = service.decidir(
                user_id=user.idusuario,
                roles=user.roles,
                cliente_id=idcliente,
                decision=request.data.get("decision"),
                motivo=request.data.get("motivo"),
                ip_address=_client_ip(request),
            )
        except OnboardingAccessError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        except AprobacionProveedorError as exc:
            detail = str(exc)
            if "no encontrada" in detail:
                return error_response("not_found", detail, "404", status_code=404)
            if "no esta pendiente" in detail.lower():
                return error_response("conflict", detail, "409", status_code=409)
            return error_response("bad_request", detail, "400", status_code=400)
        return success_response(data)


class AnularRechazoProveedorView(_OnboardingAuthenticatedView):
    """Admin soft-anula Rechazado → Rechazado_Anulado (libera NIT para nuevo O14)."""

    def post(self, request: Request, idcliente: int):
        user, err = _require_auth(request)
        if err:
            return err
        service = AprobacionProveedorService()
        try:
            data = service.anular_rechazo(
                user_id=user.idusuario,
                roles=user.roles,
                cliente_id=idcliente,
                ip_address=_client_ip(request),
            )
        except OnboardingAccessError:
            return error_response("forbidden", "Privilegios insuficientes", "403", status_code=403)
        except AprobacionProveedorError as exc:
            detail = str(exc)
            if "no encontrada" in detail:
                return error_response("not_found", detail, "404", status_code=404)
            if "solo se pueden anular" in detail.lower():
                return error_response("conflict", detail, "409", status_code=409)
            return error_response("bad_request", detail, "400", status_code=400)
        return success_response(data)


class RegistrarCuentaView(_OnboardingAuthenticatedView):
    """CU-O01 retirado — todo cliente pasa por autorregistro O14 + aprobación O16."""

    def post(self, request: Request):
        user, err = _require_auth(request)
        if err:
            return err
        return error_response(
            "gone",
            "CU-O01 retirado. Use POST /cuentas-clientes/autorregistro (O14) y aprobación (O16).",
            "410",
            status_code=status.HTTP_410_GONE,
        )


class ConfigurarCuentaView(_OnboardingAuthenticatedView):
    """CU-O12 retirado — logo cliente (O02/O03); plan diferido a Suscripciones."""

    def patch(self, request: Request, idcliente: int):
        user, err = _require_auth(request)
        if err:
            return err
        return error_response(
            "gone",
            "CU-O12 retirado. El logo lo configura el cliente; el plan se gestiona en Suscripciones.",
            "410",
            status_code=status.HTTP_410_GONE,
        )


class OnboardingLogoUploadUrlView(_OnboardingAuthenticatedView):
    def post(self, request: Request, idcliente: int):
        user, err = _require_auth(request)
        if err:
            return err
        content_type = request.data.get("content_type")
        if not content_type:
            return error_response("bad_request", "Campos invalidos", "400", status_code=400)

        access = OnboardingAccessService()
        try:
            access.require_admin_local(
                user_id=user.idusuario, roles=user.roles, cliente_id=idcliente
            )
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
            if "solo disponible" in detail.lower():
                return error_response("forbidden", detail, "403", status_code=403)
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
            if "solo disponible" in detail.lower():
                return error_response("forbidden", detail, "403", status_code=403)
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
