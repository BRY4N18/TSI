"""Catálogo **explícito** de etapas de onboarding.

No se infiere de `Fact_Onboarding`: una etapa que nadie ha completado
desaparecería del embudo, y es justo donde está el problema.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

#: Orden del proceso documentado. Las tres primeras son obligatorias en origen.
#: `verificacion_documental` y `activacion_operativa` existen en el proceso y
#: casi nunca tienen fila — el embudo tiene que mostrarlas igual.
CATALOGO: tuple[tuple[int, str, int], ...] = (
    (1, "cambio_password", 1),
    (2, "perfil_corporativo", 1),
    (3, "preferencias", 1),
    (4, "verificacion_documental", 0),
    (5, "activacion_operativa", 0),
)

ORDEN: dict[str, int] = {etapa: orden for orden, etapa, _ in CATALOGO}
OBLIGATORIAS: frozenset[str] = frozenset(
    etapa for _, etapa, obligatoria in CATALOGO if obligatoria
)


def extraer() -> list[dict]:
    """El catálogo no sale del origen: está declarado aquí."""
    return []


def construir(_filas: list[dict], ahora: datetime) -> list[dict]:
    version = ahora.strftime("%Y-%m-%d %H:%M:%S")
    return [
        {
            "idetapa": orden,
            "etapa": etapa,
            "orden": orden,
            "es_obligatoria": obligatoria,
            "version": version,
        }
        for orden, etapa, obligatoria in CATALOGO
    ]


def orden_de(etapa: Any) -> int | None:
    if etapa is None:
        return None
    return ORDEN.get(str(etapa).strip())
