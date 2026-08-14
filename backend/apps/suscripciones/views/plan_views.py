"""Views — planes (RF-SUSF-001)."""

from __future__ import annotations

from rest_framework.views import APIView

from apps.suscripciones.idempotency import get_cached_response, store_response
from apps.suscripciones.permissions import (
    IsCatalogoPlanesReader,
    IsDirectorEstrategiaBilling,
)
from apps.suscripciones.services.catalogo_plan_service import (
    CatalogoPlanError,
    CatalogoPlanService,
)
from apps.suscripciones.throttles import AdminBillingThrottle
from core.api.response_envelope import error_response, success_response


def _parse_bool(raw: str | None) -> bool | None:
    if raw is None or raw == "":
        return None
    low = str(raw).lower()
    if low in {"1", "true", "yes", "si", "sí"}:
        return True
    if low in {"0", "false", "no"}:
        return False
    raise ValueError("invalid boolean")


class SeveridadCatalogoView(APIView):
    """Catálogo de severidades para el formulario de plan (`Dim_Severidad`).

    El formulario traía las opciones escritas en duro. Leerlas de la tabla es lo
    que permite añadir o retirar una severidad sin tocar el sistema (SRS §6).
    """

    permission_classes = [IsCatalogoPlanesReader]

    def get(self, request):
        return success_response({"items": CatalogoPlanService().listar_severidades()})


class PlanListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsDirectorEstrategiaBilling()]
        return [IsCatalogoPlanesReader()]

    def get_throttles(self):
        if self.request.method == "POST":
            return [AdminBillingThrottle()]
        return []

    def get(self, request):
        try:
            cursor_raw = request.query_params.get("cursor")
            cursor = int(cursor_raw) if cursor_raw not in (None, "") else None
            if cursor is not None and cursor < 0:
                raise ValueError("cursor")
            limit = int(request.query_params.get("limit", "20"))
            if limit < 1 or limit > 100:
                raise ValueError("limit")
        except (TypeError, ValueError):
            return error_response(
                "invalid_query",
                "Parámetros cursor/limit inválidos",
                "400",
                status_code=400,
            )

        q = (request.query_params.get("q") or "").strip() or None
        nivel = (request.query_params.get("nivel") or "").strip() or None

        roles = list(getattr(request.user, "roles", []) or [])
        es_director = "DirectorEstrategia" in roles

        try:
            activo: bool | None = None
            solo_activos: bool | None = None
            if "activo" in request.query_params:
                activo = _parse_bool(request.query_params.get("activo"))
            elif "solo_activos" in request.query_params:
                solo_activos = _parse_bool(request.query_params.get("solo_activos"))
            elif not es_director:
                # Compat: no-Director que omite filtros → solo activos.
                # Director que omite activo/solo_activos → todas (OpenAPI).
                solo_activos = True
        except ValueError:
            return error_response(
                "invalid_query",
                "Parámetro activo/solo_activos inválido",
                "400",
                status_code=400,
            )

        try:
            result = CatalogoPlanService().listar(
                cursor=cursor,
                limit=limit,
                q=q,
                activo=activo,
                nivel=nivel,
                solo_activos=solo_activos,
                es_director=es_director,
            )
        except CatalogoPlanError as exc:
            return error_response(exc.code, exc.detail, "400", status_code=400)

        return success_response(
            result["items"],
            meta={
                "pagination": {
                    "next_cursor": result["next_cursor"],
                    "limit": result["limit"],
                }
            },
        )

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
    permission_classes = [IsDirectorEstrategiaBilling]
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
