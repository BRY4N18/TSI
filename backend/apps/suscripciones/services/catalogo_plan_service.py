"""RF-SUSF-001 — catálogo de planes."""

from __future__ import annotations

from typing import Any

from core.repositories.suscripciones.plan_repository import PlanRepository
from core.repositories.suscripciones.severidad_repository import SeveridadRepository

NIVELES = frozenset({"Básico", "Profesional", "Empresarial"})
PERIODICIDADES = frozenset({"Mensual", "Anual"})


class CatalogoPlanError(Exception):
    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(detail)


class CatalogoPlanService:
    def __init__(
        self,
        plans: PlanRepository | None = None,
        severidades: SeveridadRepository | None = None,
    ):
        self.plans = plans or PlanRepository()
        self.severidades = severidades or SeveridadRepository()

    def listar_severidades(self) -> list[dict[str, Any]]:
        """Catálogo vigente para alimentar el selector del formulario de plan."""
        return self.severidades.listar_activas()

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
        if "periodicidad" in changes and changes["periodicidad"] not in PERIODICIDADES:
            raise CatalogoPlanError("invalid_periodicidad", "periodicidad inválida")
        if "severidades_desbloqueadas" in changes:
            self._validate_severidades(changes["severidades_desbloqueadas"])
        if "carga_lote_habilitada" in changes:
            self._validate_carga_lote_habilitada(changes["carga_lote_habilitada"])
        if "limites" in changes:
            self._validate_limites(changes["limites"])
        if "precio_excedente_llamada" in changes:
            self._validate_precio_excedente(changes["precio_excedente_llamada"])
        updated = self.plans.update(idplan, changes)
        if not updated:
            raise CatalogoPlanError("not_found", "Plan no encontrado")
        return updated

    def _validate(self, data: dict[str, Any]) -> None:
        for field in (
            "nombre", "precio", "limites", "nivel", "periodicidad",
            "severidades_desbloqueadas", "precio_excedente_llamada",
        ):
            if field not in data:
                raise CatalogoPlanError("validation_error", f"Falta {field}")
        self._validate_precio_excedente(data["precio_excedente_llamada"])
        if data["nivel"] not in NIVELES:
            raise CatalogoPlanError("invalid_nivel", "nivel inválido")
        if data["periodicidad"] not in PERIODICIDADES:
            raise CatalogoPlanError("invalid_periodicidad", "periodicidad inválida")
        self._validate_severidades(data["severidades_desbloqueadas"])
        if "carga_lote_habilitada" in data:
            self._validate_carga_lote_habilitada(data["carga_lote_habilitada"])
        self._validate_limites(data["limites"])

    def _validate_precio_excedente(self, valor: Any) -> None:
        """RF-O54.1 — tarifa del excedente de API, anadida 2026-08-08.

        `precio` es el importe de la suscripcion; esta columna es el precio
        UNITARIO de cada llamada que supera el cupo. Sin ella, CU-O54 de
        Partners y API no puede calcular el importe del excedente.

        Se rechaza el negativo porque -1.0 es el centinela de "sin tarifa
        configurada" y no debe poder fijarse desde el formulario. El cero SI se
        admite: es una decision comercial legitima (excedente incluido), pero
        distinta de "no configurado".
        """
        try:
            precio = float(valor)
        except (TypeError, ValueError):
            raise CatalogoPlanError(
                "invalid_precio_excedente", "precio_excedente_llamada debe ser numerico"
            )
        if precio < 0:
            raise CatalogoPlanError(
                "invalid_precio_excedente", "precio_excedente_llamada no puede ser negativo"
            )

    def _validate_limites(self, limites: Any) -> None:
        """RN-SUSF-019 — `api_calls_minuto` añadido 2026-08-08.

        El SRS §3.4.1 exige que el plan de acceso defina el límite de llamadas
        "mensual y por minuto"; solo existía el mensual. El límite por minuto no
        es un prorrateo del mensual: protege contra ráfagas, y lo configura el
        Director de Estrategia al crear o editar el plan (CU-O26 / RF-O26.1).

        Sin él, Partners y API no puede derivar el cupo del partner (RF-PON-003)
        y `Dim_Partner.limitellamadasminuto` se quedaría sin origen.
        """
        if not isinstance(limites, dict):
            raise CatalogoPlanError("invalid_limites", "limites debe ser objeto")
        for k in ("unidades_max", "usuarios_max", "api_calls_mes", "api_calls_minuto"):
            if k not in limites or int(limites[k]) < 0:
                raise CatalogoPlanError("invalid_limites", f"limites.{k} inválido")

    def _validate_severidades(self, severidades: Any) -> None:
        """RN-SUSF-002 — severidad es campo independiente y totalmente
        configurable por el Director; no se deriva de `nivel`.

        Desde 2026-08-11 se guardan **identificadores de `Dim_Severidad`**, no la
        escala paralela `Baja/Media/Alta` que existía aquí y que no correspondía a
        ninguna fila del catálogo real (Leve/Moderado/Grave/Fatal). El conjunto
        válido se lee de la tabla, de modo que añadir una severidad nueva no exige
        tocar el código (SRS §6, Configurabilidad).
        """
        if not isinstance(severidades, list) or not severidades:
            raise CatalogoPlanError(
                "invalid_severidades", "severidades_desbloqueadas debe ser una lista no vacía"
            )
        try:
            ids = [int(s) for s in severidades]
        except (TypeError, ValueError):
            raise CatalogoPlanError(
                "invalid_severidades",
                "severidades_desbloqueadas debe contener identificadores de severidad",
            )
        validos = self.severidades.ids_validos()
        desconocidos = sorted(set(ids) - validos)
        if desconocidos:
            raise CatalogoPlanError(
                "invalid_severidades",
                f"severidades_desbloqueadas contiene severidades inexistentes: {desconocidos}",
            )

    def _validate_carga_lote_habilitada(self, valor: Any) -> None:
        """RF-O26.5/RF-O40.6 (2026-08-08): dato independiente y configurable por
        el Director — determina si el plan habilita la carga en lote de
        unidades (CU-O40), sin derivarse de `nivel` ni de otros campos."""
        if not isinstance(valor, bool):
            raise CatalogoPlanError(
                "invalid_carga_lote_habilitada", "carga_lote_habilitada debe ser booleano"
            )
