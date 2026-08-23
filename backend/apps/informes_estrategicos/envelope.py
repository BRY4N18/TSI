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
    denominador_actual: str | None = None,
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
    # ⚠️ **El denominador no está acotado al período, y hay que decirlo.**
    #
    # Algunos informes cuentan el numerador dentro del período y el denominador
    # sobre el estado de hoy. Pedido enero de 2019, `integraciones-activas`
    # respondía «3 partners con acceso, 0 % de adopción»: los tres son de hoy, y
    # en 2019 no existía ninguno. No era «no sabemos», era una cifra inventada
    # con forma de medición.
    #
    # Se declara en vez de corregirse porque acotar el denominador exige
    # historizar la dimensión y cambiaría lo que el informe mide. Mismo patrón
    # que `umbral_aplicado` y `medida_exacta_desde`: una convención que no se
    # puede deducir del número **viaja con el número**.
    if denominador_actual:
        meta["denominador_actual"] = denominador_actual
    return success_response(data, meta=meta)
