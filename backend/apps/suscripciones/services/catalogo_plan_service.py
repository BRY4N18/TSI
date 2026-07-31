"""RF-SUSF-001 — catálogo de planes."""

from __future__ import annotations

from typing import Any

from core.repositories.suscripciones.plan_repository import PlanRepository

NIVELES = frozenset({"Básico", "Profesional", "Empresarial"})


class CatalogoPlanError(Exception):
    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(detail)


class CatalogoPlanService:
    def __init__(self, plans: PlanRepository | None = None):
        self.plans = plans or PlanRepository()

    def listar(
        self,
        *,
        cursor: int | None = None,
        limit: int = 20,
        q: str | None = None,
        activo: bool | None = None,
        nivel: str | None = None,
        solo_activos: bool | None = None,
        es_director: bool = False,
    ) -> dict[str, Any]:
        """Listado paginado. No-Director fuerza activo=True (Decision 13)."""
        if nivel and nivel not in NIVELES:
            raise CatalogoPlanError("invalid_nivel", "nivel inválido")

        resolved_activo = activo
        if resolved_activo is None and solo_activos is not None:
            resolved_activo = True if solo_activos else None
        if not es_director:
            resolved_activo = True

        limit_i = max(1, min(int(limit or 20), 100))
        items, next_cursor = self.plans.list(
            cursor=cursor,
            limit=limit_i,
            q=q,
            activo=resolved_activo,
            nivel=nivel,
        )
        return {
            "items": items,
            "next_cursor": next_cursor,
            "limit": limit_i,
        }

    def crear(self, data: dict[str, Any]) -> dict[str, Any]:
        self._validate(data)
        return self.plans.create(data)

    def actualizar(self, idplan: int, changes: dict[str, Any]) -> dict[str, Any]:
        if "nivel" in changes and changes["nivel"] not in NIVELES:
            raise CatalogoPlanError("invalid_nivel", "nivel inválido")
        if "limites" in changes:
            self._validate_limites(changes["limites"])
        updated = self.plans.update(idplan, changes)
        if not updated:
            raise CatalogoPlanError("not_found", "Plan no encontrado")
        return updated

    def _validate(self, data: dict[str, Any]) -> None:
        for field in ("nombre", "precio", "limites", "nivel"):
            if field not in data:
                raise CatalogoPlanError("validation_error", f"Falta {field}")
        if data["nivel"] not in NIVELES:
            raise CatalogoPlanError("invalid_nivel", "nivel inválido")
        self._validate_limites(data["limites"])

    def _validate_limites(self, limites: Any) -> None:
        if not isinstance(limites, dict):
            raise CatalogoPlanError("invalid_limites", "limites debe ser objeto")
        for k in ("unidades_max", "usuarios_max", "api_calls_mes"):
            if k not in limites or int(limites[k]) < 0:
                raise CatalogoPlanError("invalid_limites", f"limites.{k} inválido")
