"""Construcción de la respuesta {data, meta} común a los 16 informes.

Reutiliza `core.api.response_envelope.success_response`; este módulo solo
arma la forma de `meta` (periodo + filtros) descrita en `data-model.md`.
"""

from __future__ import annotations

from typing import Any

from rest_framework.response import Response

from apps.informes_tacticos.periodo import Periodo
from core.api.response_envelope import success_response


def informe_response(data: Any, periodo: Periodo, filtros: dict[str, Any] | None = None) -> Response:
    meta = {"periodo": periodo.to_meta(), "filtros": filtros or {}}
    return success_response(data, meta=meta)


def informe_compuesto_response(
    data: Any, periodo: Periodo, *, materializado: bool, ultima_corrida: str | None
) -> Response:
    """Envelope de los 3 informes compuestos (data-model.md).

    `materializado=False` distingue "el DAG todavía no procesó este período"
    de "el período no tiene datos" (FR-008) — `data` va `None` en ese caso.
    """
    meta = {
        "periodo": {"desde": periodo.desde, "hasta": periodo.hasta},
        "materializado": materializado,
        "ultima_corrida": ultima_corrida,
    }
    return success_response(data if materializado else None, meta=meta)
