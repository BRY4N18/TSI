"""Las columnas que una consulta publica y las que el frontend lee.

⚠️ **Esta prueba existe porque un nombre de columna equivocado no rompe nada.**

`ot12_disponibilidad_declarada.sql` publicaba `pct_disponible` mientras el
contrato OpenAPI, el contrato de UI y la plantilla leían `pct_disponibilidad`.
No hubo error, ni `500`, ni columna vacía en el sentido visible: la pantalla
buscaba una clave que no existía, la trataba como **ausente**, y pintaba
«ausente» en las seis unidades — que es el render **correcto** para un dato que
no está.

Ese es el problema: seis unidades declaraban «no se sabe» mientras la consulta
devolvía disponibilidades reales del 100 %, 98,8 % y 93,8 %. Un nombre mal
escrito aquí se disfraza de dato faltante, y el dato faltante es una respuesta
legítima en todo este sistema.

Se comprueba sobre el **texto** de la consulta, como el resto del catálogo: el
fallo no se ve ejecutándola una vez, porque la consulta por sí sola es correcta.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.consultas import cargar  # noqa: E402

#: Columna que **cada informe tiene que publicar**, con el nombre exacto que lee
#: quien la consume. No es la lista completa de columnas: son las que ya se
#: escribieron mal alguna vez, o las que la pantalla convierte en «ausente» si
#: no las encuentra —que son las que más caro cuesta descubrir—.
COLUMNAS_EXIGIDAS = [
    ("red_operativa", "ot12_disponibilidad_declarada", "pct_disponibilidad"),
    # ⚠️ Se llamaban `sincronizadas` y `pendientes`, y la pantalla decía «0
    # sincronizadas · 50 pendientes» — lo contrario de la verdad operativa, donde
    # las 50 están marcadas como sincronizadas. Lo que cuentan es si hay instante
    # para medir la latencia, no si la evidencia llegó.
    ("emergencias", "ot24_latencia_sincronizacion", "con_instante_sincronia"),
    ("emergencias", "ot24_latencia_sincronizacion", "sin_instante_sincronia"),
]


@pytest.mark.parametrize("departamento,informe,columna", COLUMNAS_EXIGIDAS)
def test_la_consulta_publica_la_columna_con_el_nombre_del_contrato(
    departamento, informe, columna
):
    sql = cargar(informe, departamento=departamento)

    assert re.search(rf"\bAS\s+{re.escape(columna)}\b", sql), (
        f"{informe} no publica «{columna}». Si se renombró, la pantalla que la "
        f"lee no fallará: la dará por ausente y pintará «ausente» sobre datos "
        f"que sí existen."
    )
