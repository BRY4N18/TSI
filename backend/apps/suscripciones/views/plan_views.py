"""Views — planes (RF-SUSF-001)."""

from __future__ import annotations

from rest_framework.views import APIView

from apps.suscripciones.idempotency import get_cached_response, store_response
from apps.suscripciones.permissions import IsAdministradorBilling, IsProveedorOrAdminBilling
from apps.suscripciones.services.catalogo_plan_service import (
    CatalogoPlanError,
    CatalogoPlanService,
)
from apps.suscripciones.throttles import AdminBillingThrottle, ProveedorBillingWriteThrottle
from core.api.response_envelope import error_response, success_response


class PlanListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdministradorBilling()]
        return [IsProveedorOrAdminBilling()]

    def get_throttles(self):
        if self.request.method == "POST":
            return [AdminBillingThrottle()]
        return []

    def get(self, request):
        planes = CatalogoPlanService().listar(solo_activos=True)
        return success_response(planes)

    def post(self, request):
        cached = get_cached_response(request, "plan_create")
        if cached:
            return cached
        try:
            plan = CatalogoPlanService().crear(request.data)
        except CatalogoPlanError as exc:
            return error_response(exc.code, exc.detail, "400", status_code=400)
        response = success_response(plan, status_code=201)
        store_response(request, "plan_create", response)
        return response


class PlanDetailView(APIView):
    permission_classes = [IsAdministradorBilling]
    throttle_classes = [AdminBillingThrottle]

    def patch(self, request, idplan: int):
        cached = get_cached_response(request, f"plan_patch_{idplan}")
        if cached:
            return cached
        try:
            plan = CatalogoPlanService().actualizar(idplan, dict(request.data))
        except CatalogoPlanError as exc:
            code = "404" if exc.code == "not_found" else "400"
            return error_response(exc.code, exc.detail, code, status_code=int(code))
        response = success_response(plan)
        store_response(request, f"plan_patch_{idplan}", response)
        return response
