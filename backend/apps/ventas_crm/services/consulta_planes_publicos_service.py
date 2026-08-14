"""Public catalog of active subscription plans (RF-CPP-000). Read-only."""
from __future__ import annotations

import json
import logging
from typing import Any

from core.repositories.suscripciones.severidad_repository import SeveridadRepository
from core.repositories.ventas_crm.plan_lectura_repository import PlanLecturaRepository

logger = logging.getLogger(__name__)


def _parse_severidades(raw: Any) -> list[int]:
    """Dim_Plan.severidades_desbloqueadas — campo independiente y configurable
    por el Director de Estrategia (SRS §3.3.1, RN-SUSF-002).

    Guarda ids de `Dim_Severidad` desde la migración del 2026-08-11.
    """
    if isinstance(raw, list):
        valores = raw
    elif isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Dim_Plan.severidades_desbloqueadas no es JSON válido: %r", raw)
            return []
        valores = parsed if isinstance(parsed, list) else []
    else:
        return []

    ids: list[int] = []
    for v in valores:
        if isinstance(v, bool):
            continue
        try:
            ids.append(int(v))
        except (TypeError, ValueError):
            continue
    return ids


class ConsultaPlanesPublicosService:
    def __init__(self, planes=None, severidades=None):
        self.planes = planes or PlanLecturaRepository()
        self.severidades = severidades or SeveridadRepository()

    def listar(self) -> list[dict[str, Any]]:
        # El portal es público: se devuelven los nombres de severidad ya
        # resueltos, no los identificadores. Nadie que mire la vitrina tiene por
        # qué ver una clave primaria.
        nombres = self.severidades.nombres_por_id()
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
                    "severidades_desbloqueadas": [
                        nombres[i]
                        for i in _parse_severidades(row.get("severidades_desbloqueadas"))
                        if i in nombres
                    ],
                }
            )
        return out
