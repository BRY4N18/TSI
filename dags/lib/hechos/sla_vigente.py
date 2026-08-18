"""Resolución del SLA vigente en un instante: intervalo **semiabierto** `[desde, hasta)`.

El instante exacto del cambio resuelve la configuración **nueva**. Unir con la
fila vigente hoy reescribiría el cumplimiento de los tickets anteriores.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Mapping

MOTIVO_SIN_CONFIG = "sin_config"


def _momento(valor: Any) -> datetime | None:
    if valor is None or valor == "" or valor == 0:
        return None
    if isinstance(valor, datetime):
        return valor.replace(tzinfo=None)
    texto = str(valor).strip()
    if not texto or texto.startswith("1970-01-01"):
        return None
    try:
        return datetime.fromisoformat(texto.replace("Z", "").split(".")[0])
    except ValueError:
        return None


def sla_vigente_en(
    configuraciones: Iterable[Mapping[str, Any]],
    idplan: int | None,
    tipo_incidencia: str | None,
    prioridad: str | None,
    instante: datetime | None,
) -> dict[str, Any] | None:
    """Devuelve la fila vigente en `instante`, o `None` si no hay configuración.

    Ausente no es un límite por defecto: no había compromiso que medir.
    """
    if idplan is None or instante is None:
        return None
    tipo = (tipo_incidencia or "").strip().lower()
    prio = (prioridad or "").strip().lower()
    if not tipo or not prio:
        return None

    candidatas: list[tuple[datetime, Mapping[str, Any]]] = []
    for fila in configuraciones:
        try:
            plan = int(fila["idplan"])
        except (KeyError, TypeError, ValueError):
            continue
        if plan != int(idplan):
            continue
        if (fila.get("tipo_incidencia") or "").strip().lower() != tipo:
            continue
        if (fila.get("prioridad") or "").strip().lower() != prio:
            continue
        desde = _momento(fila.get("valido_desde"))
        if desde is None:
            continue
        hasta = _momento(fila.get("valido_hasta"))
        if instante < desde:
            continue
        if hasta is not None and instante >= hasta:
            continue
        candidatas.append((desde, fila))

    if not candidatas:
        return None
    candidatas.sort(key=lambda par: par[0], reverse=True)
    return dict(candidatas[0][1])
