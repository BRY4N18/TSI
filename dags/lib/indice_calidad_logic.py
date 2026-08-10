"""Lógica pura de combinación del índice consolidado de calidad (US2).

Fórmula (data-model.md): promedio simple de los 4 componentes, normalizados
a "más alto = mejor calidad" (descarte/fusión se invierten antes de promediar).
"""

from __future__ import annotations


def combinar_indice(
    pct_completitud: float,
    pct_descarte: float,
    pct_fusion: float,
    pct_cobertura_evidencia: float,
) -> float:
    componentes = [
        pct_completitud,
        1 - pct_descarte,
        1 - pct_fusion,
        pct_cobertura_evidencia,
    ]
    return round(sum(componentes) / len(componentes), 4)
