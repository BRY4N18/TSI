"""RN-SEV-COHERENCIA — la severidad declarada debe sostenerse con las víctimas.

Motivación (revisión 24/08/2026, hallazgo #4)
---------------------------------------------
El sistema aceptaba un accidente con 200 heridos marcado como **Leve**. Nada
comparaba `idseveridad` contra `numheridos`/`numfallecidos`: la severidad era un
dato declarado y punto. Como la severidad es lo que gobierna el despacho, un
"Leve" mentido —o simplemente mal elegido— manda la unidad equivocada.

Que exista "Escalar severidad" no cubría el hueco: escalar corrige *después*,
cuando la unidad ya llegó al sitio, y esa es precisamente la llamada que se
decidió mal.

Qué hace y qué no
-----------------
Esto **no adivina** la severidad ni la sobrescribe: quien registra sigue
decidiendo. Lo que hace es exigir un piso mínimo demostrable a partir de datos
que el propio formulario ya captura, y distinguir dos niveles de exigencia:

- **Bloqueante** cuando el dato contradice frontalmente lo declarado (hay
  fallecidos y se declara no-fatal; hay heridos masivos y se declara leve).
- **Advertencia** cuando es sospechoso pero puede ser legítimo — el operador
  confirma y sigue, que es el mecanismo que ya usa `ValidacionAccidenteService`
  para "fuera de cobertura" y "posible duplicado".

El catálogo canónico de severidades es `Dim_Severidad` (ver
`database/seed_severidad.py`): el id **es** el nivel de gravedad, orden
ascendente.
"""

from __future__ import annotations

from typing import Any

SEVERIDAD_LEVE = 1
SEVERIDAD_MODERADO = 2
SEVERIDAD_GRAVE = 3
SEVERIDAD_FATAL = 4

SEVERIDAD_LABEL = {
    SEVERIDAD_LEVE: "Leve",
    SEVERIDAD_MODERADO: "Moderado",
    SEVERIDAD_GRAVE: "Grave",
    SEVERIDAD_FATAL: "Fatal",
}

#: A partir de cuántos heridos un accidente deja de poder llamarse "Leve".
UMBRAL_HERIDOS_GRAVE = 5

CODE_SEVERIDAD_INCOHERENTE = "severidad_incoherente"
CODE_SEVERIDAD_SOSPECHOSA = "severidad_sospechosa"


def _entero(valor: Any) -> int:
    """Normaliza un conteo que puede llegar como None, "" o string numérico.

    Los conteos viajan por JSON y por CSV; asumir `int` acababa en TypeError
    (500) en vez de en una validación.
    """
    if valor in (None, ""):
        return 0
    try:
        return int(valor)
    except (TypeError, ValueError):
        return 0


def severidad_minima_exigible(*, numheridos: Any, numfallecidos: Any) -> int:
    """Piso de severidad que los conteos sostienen por sí solos."""
    fallecidos = _entero(numfallecidos)
    heridos = _entero(numheridos)
    if fallecidos >= 1:
        return SEVERIDAD_FATAL
    if heridos >= UMBRAL_HERIDOS_GRAVE:
        return SEVERIDAD_GRAVE
    if heridos >= 1:
        return SEVERIDAD_MODERADO
    return SEVERIDAD_LEVE


def evaluar(
    *, idseveridad: Any, numheridos: Any, numfallecidos: Any
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Evalúa la coherencia. Retorna `(bloqueantes, advertencias)`.

    Ambas listas usan la forma `{"code", "detail"}` de `ValidationResult`, para
    que el llamador las concatene sin traducir nada.
    """
    bloqueantes: list[dict[str, str]] = []
    advertencias: list[dict[str, str]] = []

    declarada = _entero(idseveridad)
    if declarada not in SEVERIDAD_LABEL:
        # La validación del enum no es asunto de este módulo; sin una severidad
        # reconocible no hay coherencia que evaluar.
        return bloqueantes, advertencias

    heridos = _entero(numheridos)
    fallecidos = _entero(numfallecidos)
    minima = severidad_minima_exigible(numheridos=heridos, numfallecidos=fallecidos)

    if declarada < minima:
        detalle = (
            f"Se declaró severidad {SEVERIDAD_LABEL[declarada]} con "
            f"{heridos} herido(s) y {fallecidos} fallecido(s). "
            f"Ese registro exige al menos {SEVERIDAD_LABEL[minima]}."
        )
        # Fallecidos y heridos masivos no admiten interpretación: bloquean.
        # Un solo herido con "Leve" sí puede ser un rasguño: se advierte.
        if minima >= SEVERIDAD_GRAVE:
            bloqueantes.append({"code": CODE_SEVERIDAD_INCOHERENTE, "detail": detalle})
        else:
            advertencias.append({"code": CODE_SEVERIDAD_SOSPECHOSA, "detail": detalle})

    # Coherencia por arriba: un Fatal sin una sola víctima suele ser un error de
    # captura. No se bloquea —puede haber daños catastróficos sin heridos— pero
    # se dice.
    if declarada == SEVERIDAD_FATAL and fallecidos == 0:
        advertencias.append(
            {
                "code": CODE_SEVERIDAD_SOSPECHOSA,
                "detail": (
                    "Se declaró severidad Fatal sin fallecidos registrados. "
                    "Confirme el conteo de víctimas."
                ),
            }
        )

    return bloqueantes, advertencias
