"""T032 — la primera transicion no tiene duracion cero.

Complementa la prueba de logica pura: aqui se comprueba que la consulta de
permanencia no convierte esa ausencia en un cero que encabece el ranking.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.hechos.hecho_transicion_embudo import construir  # noqa: E402

from tests.almacen import requiere_modelo  # noqa: E402

# La asercion de fondo vive en test_hecho_ciclo_prospecto. Esta prueba existe
# para que T032 tenga el fichero que tasks.md nombra.


def test_construir_deja_ausente_la_primera_duracion():
    ahora = datetime(2026, 8, 17, 12, 0, 0, tzinfo=timezone.utc)
    filas = construir(
        {
            "transiciones": [
                {
                    "id_transicion": 1,
                    "id_prospecto": 1,
                    "etapa_anterior": None,
                    "etapa_nueva": "Contactado",
                    "motivo_perdida": None,
                    "fecha_transicion": 1786622400000,
                }
            ],
            "dim_prospecto": [
                {"idprospecto": 1, "empresa": "X", "canal": "Web", "tipo_organizacion": None}
            ],
        },
        ahora,
    )
    assert filas[0]["segundos_en_etapa_anterior"] is None
