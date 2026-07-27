"""Public catalog of active subscription plans (RF-CPP-000). Read-only."""
from __future__ import annotations

import logging
import unicodedata
from typing import Any

from core.repositories.ventas_crm.plan_lectura_repository import PlanLecturaRepository

logger = logging.getLogger(__name__)

_SEVERIDADES_POR_NIVEL: dict[str, list[str]] = {
    "basico": ["Baja"],
    "profesional": ["Baja", "Media"],
    "empresarial": ["Baja", "Media", "Alta"],
}


def _normalize_nivel(nivel: str | None) -> str:
    raw = (nivel or "").strip().lower()
    # strip accents: básico -> basico
    return "".join(
        c for c in unicodedata.normalize("NFD", raw) if unicodedata.category(c) != "Mn"
    )


def severidades_para_nivel(nivel: str | None) -> list[str]:
    key = _normalize_nivel(nivel)
    if key not in _SEVERIDADES_POR_NIVEL:
        logger.warning("Dim_Plan.nivel desconocido para severidades: %r", nivel)
        return []
    return list(_SEVERIDADES_POR_NIVEL[key])


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
                    "severidades_desbloqueadas": severidades_para_nivel(row.get("nivel")),
                }
            )
        return out
