"""Views — cambio de plan."""

from __future__ import annotations

from rest_framework.views import APIView

from apps.suscripciones.idempotency import get_cached_response, store_response
from apps.suscripciones.permissions import IsAdministradorBilling, IsProveedorCuenta, IsProveedorOrAdminBilling
from apps.suscripciones.services.cambio_plan_service import CambioPlanError, CambioPlanService
from apps.suscripciones.throttles import AdminBillingThrottle, ProveedorBillingWriteThrottle
from core.api.response_envelope import error_response, success_response
from core.repositories.suscripciones.solicitud_cambio_plan_repository import (
    SolicitudCambioPlanRepository,
)


class SolicitudCambioPlanListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsProveedorCuenta()]
        return [IsProveedorOrAdminBilling()]

    def get_throttles(self):
        if self.request.method == "POST":
            return [ProveedorBillingWriteThrottle()]
        return []

    def get(self, request):
        estado = request.query_params.get("estado")
        roles = list(getattr(request.user, "roles", []) or [])
        if "Administrador" in roles:
            idcliente = request.query_params.get("idcliente")
            cid = int(idcliente) if idcliente not in (None, "") else None
            items = SolicitudCambioPlanRepository().list(idcliente=cid, estado=estado)
        else:
            items = SolicitudCambioPlanRepository().list(
                idcliente=request.billing_idcliente, estado=estado
            )
        return success_response(items)

    def post(self, request):
        cached = get_cached_response(request, "solicitud_cambio_plan")
        if cached:
            return cached
        idplan = request.data.get("idplansolicitado")
        if idplan is None:
            return error_response(
                "validation_error", "idplansolicitado requerido", "400", status_code=400
            )
        try:
            sol = CambioPlanService().solicitar(
                idcliente=request.billing_idcliente,
                idplansolicitado=int(idplan),
                motivo=request.data.get("motivo", ""),
            )
        except CambioPlanError as exc:
            return error_response(
                exc.code, exc.detail, str(exc.http_status), status_code=exc.http_status
            )
        response = success_response(sol, status_code=201)
        store_response(request, "solicitud_cambio_plan", response)
        return response


class AprobarCambioPlanView(APIView):
    permission_classes = [IsAdministradorBilling]
    throttle_classes = [AdminBillingThrottle]

    def post(self, request, idsolicitud: int):
        cached = get_cached_response(request, f"aprobar_cambio_{idsolicitud}")
        if cached:
            return cached
        try:
            sol = CambioPlanService().aprobar(
                idsolicitud=idsolicitud, idadmin=request.user.idusuario
            )
        except CambioPlanError as exc:
            return error_response(
                exc.code, exc.detail, str(exc.http_status), status_code=exc.http_status
            )
        response = success_response(sol)
        store_response(request, f"aprobar_cambio_{idsolicitud}", response)
        return response


class RechazarCambioPlanView(APIView):
    permission_classes = [IsAdministradorBilling]
    throttle_classes = [AdminBillingThrottle]

    def post(self, request, idsolicitud: int):
        cached = get_cached_response(request, f"rechazar_cambio_{idsolicitud}")
        if cached:
            return cached
        motivo = request.data.get("motivo_rechazo", "")
        if not motivo:
            return error_response(
                "validation_error", "motivo_rechazo requerido", "400", status_code=400
            )
        try:
            sol = CambioPlanService().rechazar(
                idsolicitud=idsolicitud,
                idadmin=request.user.idusuario,
                motivo_rechazo=motivo,
            )
        except CambioPlanError as exc:
            return error_response(
                exc.code, exc.detail, str(exc.http_status), status_code=exc.http_status
            )
        response = success_response(sol)
        store_response(request, f"rechazar_cambio_{idsolicitud}", response)
        return response
