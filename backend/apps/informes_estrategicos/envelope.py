"""Respuesta `{data, meta}` de la capa estratégica.

`meta` declara período, comparación, objetivo, cobertura, y —cuando hace falta—
`falta` y `alcance`. **No emite `acotado_a`**: estos informes no acotan por
titularidad, y un `todos` fijo no significaría nada.
"""

from __future__ import annotations

from typing import Any

from rest_framework.response import Response

from apps.informes_estrategicos.periodo_estrategico import PeriodoEstrategico
from core.api.response_envelope import success_response


def informe_estrategico_response(
    data: Any,
    periodo: PeriodoEstrategico,
    *,
    comparacion: dict[str, Any] | None = None,
    objetivo: dict[str, Any] | None = None,
    cobertura: str = "completa",
    falta: list[str] | None = None,
    alcance: str | None = None,
) -> Response:
    meta: dict[str, Any] = {
        "periodo": periodo.to_meta(),
        "cobertura": cobertura,
    }
    if comparacion is not None:
        meta["comparacion"] = comparacion
    if objetivo is not None:
        meta["objetivo"] = objetivo
    if falta:
        meta["falta"] = falta
    if alcance:
        meta["alcance"] = alcance
    return success_response(data, meta=meta)
