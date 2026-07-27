"""Views — historial de facturas."""

from __future__ import annotations

from rest_framework.views import APIView

from apps.suscripciones.permissions import IsProveedorCuenta
from apps.suscripciones.services.historial_factura_service import HistorialFacturaService
from core.api.response_envelope import error_response, success_response


class FacturaListView(APIView):
    permission_classes = [IsProveedorCuenta]

    def get(self, request):
        limit = int(request.query_params.get("limit", 20))
        items = HistorialFacturaService().listar(request.billing_idcliente, limit=limit)
        return success_response(items)


class FacturaDetailView(APIView):
    permission_classes = [IsProveedorCuenta]

    def get(self, request, id_factura: str):
        fac = HistorialFacturaService().detalle(request.billing_idcliente, id_factura)
        if not fac:
            return error_response("not_found", "Factura no encontrada", "404", status_code=404)
        return success_response(fac)
