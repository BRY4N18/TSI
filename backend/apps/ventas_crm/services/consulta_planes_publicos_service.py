"""Public catalog of active subscription plans (RF-CPP-000). Read-only."""
from __future__ import annotations

import json
import logging
from typing import Any

from core.repositories.ventas_crm.plan_lectura_repository import PlanLecturaRepository

logger = logging.getLogger(__name__)


def _parse_severidades(raw: Any) -> list[str]:
    """Dim_Plan.severidades_desbloqueadas — campo independiente y configurable
    por el Director de Estrategia (corrección 2026-08-08: ya NO se deriva de `nivel`,
    ver SRS §3.3.1 y RN-SUSF-002)."""
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            logger.warning("Dim_Plan.severidades_desbloqueadas no es JSON válido: %r", raw)
            return []
    return []


class ConsultaPlanesPublicosService:
    def __init__(self, planes=None):
        self.planes = planes or PlanLecturaRepository()

    def listar(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for row in self.planes.list_activos():
            out.append(
                {
                    "idplan": row["idplan"],
                    "nombre": row.get("nombre"),
                    "precio": row.get("precio"),
                    "limites": row.get("limites") if row.get("limites") is not None else "",
                    "nivel": row.get("nivel"),
                    "periodicidad": row.get("periodicidad") or "Mensual",
                    "severidades_desbloqueadas": _parse_severidades(
                        row.get("severidades_desbloqueadas")
                    ),
                }
            )
        return out
