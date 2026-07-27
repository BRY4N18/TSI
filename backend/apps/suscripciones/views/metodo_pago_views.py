"""Views — método de pago."""

from __future__ import annotations

from rest_framework.views import APIView

from apps.suscripciones.idempotency import get_cached_response, store_response
from apps.suscripciones.permissions import IsProveedorCuenta
from apps.suscripciones.services.metodo_pago_service import MetodoPagoError, MetodoPagoService
from apps.suscripciones.throttles import ProveedorBillingWriteThrottle
from core.api.response_envelope import error_response, success_response


class MetodoPagoListCreateView(APIView):
    permission_classes = [IsProveedorCuenta]

    def get_throttles(self):
        if self.request.method == "POST":
            return [ProveedorBillingWriteThrottle()]
        return []

    def get(self, request):
        items = MetodoPagoService().listar(request.billing_idcliente)
        return success_response(items)

    def post(self, request):
        cached = get_cached_response(request, "metodo_pago_create")
        if cached:
            return cached
        tipo = request.data.get("tipo")
        datos = request.data.get("datos_pasarela") or request.data
        try:
            result = MetodoPagoService().registrar(
                idcliente=request.billing_idcliente,
                tipo=tipo,
                datos_pasarela=datos if isinstance(datos, dict) else {},
            )
        except MetodoPagoError as exc:
            return error_response(exc.code, exc.detail, "400", status_code=400)
        response = success_response(result["metodo"], status_code=201)
        store_response(request, "metodo_pago_create", response)
        return response
