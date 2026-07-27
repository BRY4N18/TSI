"""Views — suscripción propia, alta, cancelación, reintento cobro."""

from __future__ import annotations

from rest_framework.views import APIView

from apps.suscripciones.idempotency import get_cached_response, store_response
from apps.suscripciones.permissions import IsProveedorCuenta
from apps.suscripciones.services.alta_suscripcion_service import (
    AltaSuscripcionError,
    AltaSuscripcionService,
)
from apps.suscripciones.services.cancelacion_suscripcion_service import (
    CancelacionError,
    CancelacionSuscripcionService,
)
from apps.suscripciones.services.consulta_suscripcion_service import ConsultaSuscripcionService
from apps.suscripciones.services.mora_suscripcion_service import MoraSuscripcionService
from apps.suscripciones.throttles import ProveedorBillingWriteThrottle
from core.api.response_envelope import error_response, success_response
from core.repositories.suscripciones.plan_repository import PlanRepository


class AltaSuscripcionView(APIView):
    permission_classes = [IsProveedorCuenta]
    throttle_classes = [ProveedorBillingWriteThrottle]

    def post(self, request):
        cached = get_cached_response(request, "alta_suscripcion")
        if cached:
            return cached
        idplan = request.data.get("idplan")
        if idplan is None:
            return error_response("validation_error", "idplan requerido", "400", status_code=400)
        try:
            result = AltaSuscripcionService().ejecutar(
                idcliente=request.billing_idcliente,
                idplan=int(idplan),
                renovacionautomatica=bool(request.data.get("renovacionautomatica", True)),
            )
        except AltaSuscripcionError as exc:
            return error_response(
                exc.code, exc.detail, str(exc.http_status), status_code=exc.http_status
            )
        response = success_response(result["suscripcion"], status_code=201)
        store_response(request, "alta_suscripcion", response)
        return response


class MiSuscripcionView(APIView):
    permission_classes = [IsProveedorCuenta]

    def get(self, request):
        svc = ConsultaSuscripcionService()
        sus = svc.mi_suscripcion(request.billing_idcliente)
        if not sus:
            return error_response("not_found", "Sin suscripción", "404", status_code=404)
        plan = PlanRepository().find_by_id(sus.get("idplan"))
        payload = {
            **sus,
            "acceso_permitido": svc.acceso_permitido(request.billing_idcliente),
            "plan_nombre": plan.get("nombre") if plan else None,
            "nivel": plan.get("nivel") if plan else None,
        }
        return success_response(payload)


class CancelarSuscripcionView(APIView):
    permission_classes = [IsProveedorCuenta]
    throttle_classes = [ProveedorBillingWriteThrottle]

    def post(self, request):
        cached = get_cached_response(request, "cancelar_suscripcion")
        if cached:
            return cached
        motivo = request.data.get("motivocancelacion", "")
        try:
            sus = CancelacionSuscripcionService().cancelar(
                idcliente=request.billing_idcliente,
                motivocancelacion=motivo,
            )
        except CancelacionError as exc:
            return error_response(
                exc.code, exc.detail, str(exc.http_status), status_code=exc.http_status
            )
        response = success_response(sus)
        store_response(request, "cancelar_suscripcion", response)
        return response


class ReintentarCobroView(APIView):
    permission_classes = [IsProveedorCuenta]
    throttle_classes = [ProveedorBillingWriteThrottle]

    def post(self, request):
        cached = get_cached_response(request, "reintentar_cobro")
        if cached:
            return cached
        sus = ConsultaSuscripcionService().mi_suscripcion(request.billing_idcliente)
        if not sus or sus.get("estado") != "Suspendida":
            return error_response(
                "conflict",
                "No hay suscripción Suspendida",
                "409",
                status_code=409,
            )
        result = MoraSuscripcionService().regularizar(id_suscripcion=sus["id_suscripcion"])
        if result.get("estado_pago") is None:
            return error_response(
                "conflict",
                "No hay factura Fallida vigente",
                "409",
                status_code=409,
            )
        response = success_response(result)
        store_response(request, "reintentar_cobro", response)
        return response
