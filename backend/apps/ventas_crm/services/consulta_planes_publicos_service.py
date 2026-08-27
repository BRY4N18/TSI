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
    def __init__(self, planes=None, severidades=None, pinot=None):
        self.planes = planes or PlanLecturaRepository()
        self.severidades = severidades or SeveridadRepository()
        self.pinot = pinot or getattr(self.planes, "pinot", None)

    def _obtener_conteos_suscripciones(self) -> dict[int, int]:
        """Consulta en Fact_Suscripcion los planes más usados con suscripción activa."""
        if not self.pinot:
            return {}
        try:
            rows = self.pinot.query(
                "SELECT idplan, count(*) AS total FROM Fact_Suscripcion WHERE estado = 'Activa' GROUP BY idplan ORDER BY total DESC LIMIT 20"
            ) or []
            conteos: dict[int, int] = {}
            for r in rows:
                idp = r.get("idplan")
                if idp is not None:
                    try:
                        conteos[int(idp)] = int(r.get("total", 0))
                    except (ValueError, TypeError):
                        continue
            return conteos
        except Exception:
            logger.warning("No se pudo consultar métricas de popularidad de planes en Pinot.")
            return {}

    def listar(self) -> list[dict[str, Any]]:
        # El portal es público: se devuelven los nombres de severidad ya
        # resueltos, no los identificadores. Nadie que mire la vitrina tiene por
        # qué ver una clave primaria.
        nombres = self.severidades.nombres_por_id()
        filas = self.planes.list_activos()
        conteos = self._obtener_conteos_suscripciones()

        # Determinar el ID del plan comercial con mayor cantidad de suscripciones activas
        id_mas_usado = None
        if conteos:
            planes_activos = {row["idplan"]: row for row in filas}
            # Filtrar solo planes activos con precio comercial (> 0)
            conteos_validos = {
                k: v for k, v in conteos.items()
                if k in planes_activos and (planes_activos[k].get("precio") or 0) > 0 and v > 0
            }
            if conteos_validos:
                id_mas_usado = max(conteos_validos, key=conteos_validos.get)

        # Si aún no hay suscripciones activas en la BD, se asigna como recomendado único al plan comercial estándar
        if id_mas_usado is None:
            for row in filas:
                if (row.get("nivel") or "").lower() == "profesional" and (row.get("precio") or 0) > 0:
                    id_mas_usado = row["idplan"]
                    break

        out: list[dict[str, Any]] = []
        for row in filas:
            es_destacado = (id_mas_usado is not None and row["idplan"] == id_mas_usado)
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
                    "destacado": es_destacado,
                    "suscripciones_activas": conteos.get(row["idplan"], 0),
                }
            )
        return out
