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

    def listar(self, *, solo_activos: bool = True) -> list[dict[str, Any]]:
        return self.plans.list(solo_activos=solo_activos)

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
