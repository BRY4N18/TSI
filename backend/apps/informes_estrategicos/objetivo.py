"""Metas del BSC: lo que es un compromiso y lo que es una conjetura.

`cumple` es `null` siempre que `tipo` sea `CALIBRAR`. No es un `false`
pendiente de comprobar: es la afirmación de que la pregunta no se puede
responder todavía porque el umbral no está calibrado contra nada.

Pintar en rojo un `[CALIBRAR]` presenta como fracaso una meta que nadie midió
nunca. Hoy **todos** los objetivos propios de OE6 son `CALIBRAR`.
"""

from __future__ import annotations

from typing import Any

TIPOS = ("NORMATIVO", "CALIBRAR")


def construir_objetivo(
    *,
    tipo: str,
    valor: float | int | None = None,
    unidad: str | None = None,
    medido: float | int | None = None,
    umbral: str = "le",
) -> dict[str, Any]:
    """Arma `meta.objetivo`.

    `medido` se ignora cuando `tipo` es `CALIBRAR`: aunque se pase un valor
    medido, `cumple` sigue siendo `null`. Un semáforo aquí inventaría el umbral
    y luego se mediría contra él.

    `umbral` solo aplica a `NORMATIVO`: `lt` / `le` / `gt` / `ge`.
    """
    if tipo not in TIPOS:
        raise ValueError(f"tipo de objetivo '{tipo}' no soportado, use una de: {list(TIPOS)}.")

    cumple: bool | None
    if tipo == "CALIBRAR":
        cumple = None
    elif medido is None or valor is None:
        cumple = None
    elif umbral == "lt":
        cumple = medido < valor
    elif umbral == "le":
        cumple = medido <= valor
    elif umbral == "gt":
        cumple = medido > valor
    elif umbral == "ge":
        cumple = medido >= valor
    else:
        raise ValueError(f"umbral '{umbral}' no soportado.")

    return {
        "valor": valor,
        "unidad": unidad,
        "tipo": tipo,
        "cumple": cumple,
    }


def objetivo_calibrar(*, valor: float | int | None = None, unidad: str | None = None) -> dict[str, Any]:
    return construir_objetivo(tipo="CALIBRAR", valor=valor, unidad=unidad)


def objetivo_normativo(
    *,
    valor: float | int,
    unidad: str | None,
    medido: float | int | None,
    umbral: str = "lt",
) -> dict[str, Any]:
    return construir_objetivo(
        tipo="NORMATIVO", valor=valor, unidad=unidad, medido=medido, umbral=umbral
    )
