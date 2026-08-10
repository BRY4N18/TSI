"""Lectura de la suscripcion vigente y su plan (RF-PON-003, RN-PON-011).

SOLO LECTURA. `Fact_Suscripcion` y `Dim_Plan` pertenecen a
`subscriptions-and-billing`; este modulo nunca los escribe.
"""

from __future__ import annotations

import json
from typing import Any

from core.pinot.client import PinotClient

# Estados de Fact_Suscripcion que habilitan la incorporacion de un partner.
# Una suscripcion suspendida o cancelada no da derecho a cupo (RN-PON-011).
ESTADOS_VIGENTES = frozenset({"Activa", "Activo"})


class PlanReadError(Exception):
    """No se pudo derivar el cupo. Lleva un `code` para mapear la respuesta HTTP."""

    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(detail)


class PlanReadRepository:
    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def suscripcion_vigente(self, idcliente: int) -> dict[str, Any] | None:
        """La suscripcion activa del cliente, o None si no tiene."""
        rows = self.pinot.query(
            "SELECT * FROM Fact_Suscripcion WHERE idcliente = %(idcliente)s "
            "ORDER BY fecha_inicio DESC LIMIT 50",
            {"idcliente": idcliente},
        )
        for row in rows:
            if row.get("estado") in ESTADOS_VIGENTES and row.get("activo", True):
                return row
        return None

    def find_plan(self, idplan: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            "SELECT * FROM Dim_Plan WHERE idplan = %(idplan)s LIMIT 1", {"idplan": idplan}
        )
        return rows[0] if rows else None

    def cupo_del_cliente(self, idcliente: int) -> dict[str, Any]:
        """RF-PON-003 — deriva el cupo del plan contratado; no se elige libremente.

        Devuelve `{nombre_plan, api_calls_mes, api_calls_minuto}`.

        Lanza `PlanReadError`:
          - `sin_suscripcion`  -> 422 (RN-PON-011)
          - `plan_incompleto`  -> 422 si `limites` no declara ambos limites

        Se prefiere fallar visiblemente antes que asumir un cupo: el cupo es la
        base del calculo de excedente de CU-O54, y un valor inventado seria
        dinero mal cobrado sin que nadie se entere.
        """
        suscripcion = self.suscripcion_vigente(idcliente)
        if not suscripcion:
            raise PlanReadError(
                "sin_suscripcion", "El cliente no tiene una suscripción vigente"
            )

        plan = self.find_plan(int(suscripcion["idplan"]))
        if not plan:
            raise PlanReadError(
                "plan_incompleto", "La suscripción referencia un plan inexistente"
            )

        try:
            limites = json.loads(plan.get("limites") or "{}")
        except (TypeError, json.JSONDecodeError):
            raise PlanReadError(
                "plan_incompleto", "El plan tiene `limites` con formato inválido"
            )

        faltan = [k for k in ("api_calls_mes", "api_calls_minuto") if k not in limites]
        if faltan:
            raise PlanReadError(
                "plan_incompleto",
                f"El plan no declara {', '.join(faltan)} en sus límites",
            )

        return {
            "nombre_plan": plan.get("nombre"),
            "api_calls_mes": int(limites["api_calls_mes"]),
            "api_calls_minuto": int(limites["api_calls_minuto"]),
        }
