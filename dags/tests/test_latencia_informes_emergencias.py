"""T072 — los 26 informes responden en tiempo aceptable (SC-009).

⚠️ **Con al menos tres meses de datos, y eso es la mitad de la prueba.** Un
informe sobre un día responde rápido siempre, incluso si su consulta recorre la
tabla entera: no hay bastantes filas para que se note. El particionado solo se
ejercita cuando el rango abarca varias particiones, y es ahí donde un `WHERE` mal
puesto —que impida podar particiones— pasa de ser gratis a costar la tabla
completa.

Qué es «aceptable» aquí
------------------------
El tope es generoso a propósito. Esta prueba no mide rendimiento: **detecta la
consulta que se fue de escala**, la que pasa de milisegundos a decenas de
segundos porque perdió la poda de particiones o porque un `JOIN` se volvió
cuadrático. Un umbral ajustado fallaría por el ruido de una máquina cargada y
acabaría desactivado, que es la peor forma de no tener prueba.

El repositorio impone además `max_execution_time = 30` en el servidor, así que
una consulta desbocada se corta sola. Esto vigila el escalón anterior.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import requiere_modelo  # noqa: E402

from lib.clickhouse_http_client import query_clickhouse  # noqa: E402
from lib.consultas import cargar, listar  # noqa: E402

INFORMES = listar("emergencias")

#: Seis meses y medio: todo el rango con datos, ocho particiones mensuales.
PERIODO = {"desde": "2026-02-01", "hasta": "2026-08-31"}

EXTRA = {
    "umbral_seg": "60", "ventana_dias": "90", "muestra_minima": "5",
    "top": "10", "tramos_dias": "1,3,7,30",
}

#: Segundos. Ver el docstring: detecta el salto de escala, no el rendimiento.
TOPE = 10.0


@requiere_modelo
class TestLatencia:
    @pytest.mark.parametrize("informe", INFORMES)
    def test_responde_dentro_del_tope(self, informe):
        inicio = time.monotonic()
        query_clickhouse(
            cargar(informe, departamento="emergencias"), params={**PERIODO, **EXTRA}
        )
        transcurrido = time.monotonic() - inicio

        assert transcurrido < TOPE, (
            f"'{informe}' tardó {transcurrido:.1f}s sobre siete meses de datos: "
            f"a esa escala el salto suele ser poda de particiones perdida"
        )

    def test_el_periodo_de_prueba_abarca_varias_particiones(self):
        """Sin esto, la prueba anterior pasaría sobre un solo día y no diría nada.

        Las particiones son mensuales, así que se comprueba que el rango cruza
        varios meses **y** que hay filas en ellos: un rango amplio sobre una tabla
        vacía se recorre igual de rápido que un día.
        """
        particiones = query_clickhouse(
            "SELECT uniqExact(toYYYYMM(fecha)) AS n, count() AS filas "
            "FROM hecho_accidente FINAL "
            f"WHERE fecha BETWEEN '{PERIODO['desde']}' AND '{PERIODO['hasta']}'"
        )[0]

        assert int(particiones["n"]) >= 3, (
            f"el período de prueba abarca {particiones['n']} particiones: el "
            f"particionado no se está ejercitando"
        )
        assert int(particiones["filas"]) > 1000
