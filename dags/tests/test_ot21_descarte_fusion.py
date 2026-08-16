"""T026 — descartado, fusionado y cerrado no se confunden.

Los tres suenan a «el caso ya no está activo» y significan cosas distintas:

* **descartado** — se decidió que no era un accidente real (falsa alarma).
* **fusionado** — sí era real, pero era el mismo suceso que otro caso ya abierto.
* **cerrado** — era real, se atendió y terminó. Es el desenlace normal.

Contarlos juntos convierte «hemos atendido 3000 casos» en una tasa de descarte
del 100 %. Y confundir descarte con fusión es peor de lo que parece: un pico de
descartes apunta a que la gente reporta mal, y un pico de fusiones apunta a que
el sistema no está detectando duplicados. Son dos problemas distintos con dos
responsables distintos.

Que los tres rasgos sean independientes en el constructor de casos no es un
detalle del ayudante: es que en el dominio lo son.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    cargar_casos,
    caso,
    ejecutar_informe,
    limpiar_particion,
    requiere_modelo,
)


@pytest.fixture
def particion_limpia():
    limpiar_particion()
    yield
    limpiar_particion()


@requiere_modelo
class TestCadaUnoCuentaEnLoSuyo:
    def test_tres_casos_uno_de_cada_cuentan_por_separado(self, particion_limpia):
        cargar_casos([
            caso("T026-descartado", descartado=True),
            caso("T026-fusionado", duplicado=True),
            caso("T026-cerrado", cerrado=True),
        ])

        fila = ejecutar_informe("ot21_descarte_fusion")[0]

        assert fila["casos"] == 3
        assert fila["descartados"] == 1, "el descartado no se contó, o se contó otro con él"
        assert fila["fusionados"] == 1, "el fusionado no se contó, o se contó otro con él"

    def test_un_caso_cerrado_no_cuenta_ni_como_descarte_ni_como_fusion(self, particion_limpia):
        # El desenlace normal. Si contara, la tasa de descarte de un mes bueno
        # sería del 100 % y nadie sabría distinguirla de un mes catastrófico.
        cargar_casos([caso("T026-cerrado", cerrado=True), caso("T026-abierto")])

        fila = ejecutar_informe("ot21_descarte_fusion")[0]

        assert fila["descartados"] == 0
        assert fila["fusionados"] == 0
        assert fila["pct_descarte"] == 0.0
        assert fila["pct_fusion"] == 0.0

    def test_un_caso_descartado_y_duplicado_a_la_vez_cuenta_en_ambos(self, particion_limpia):
        # No son excluyentes: un duplicado puede además descartarse. Las dos
        # cifras miden cosas distintas sobre el mismo conjunto, así que suman por
        # separado y **no** tienen por qué sumar el total entre ellas.
        cargar_casos([caso("T026-ambos", descartado=True, duplicado=True), caso("T026-normal")])

        fila = ejecutar_informe("ot21_descarte_fusion")[0]

        assert fila["casos"] == 2
        assert fila["descartados"] == 1
        assert fila["fusionados"] == 1

    def test_los_porcentajes_se_calculan_sobre_el_total_del_periodo(self, particion_limpia):
        cargar_casos([
            caso("T026-d", descartado=True),
            caso("T026-n1"),
            caso("T026-n2"),
            caso("T026-n3"),
        ])

        fila = ejecutar_informe("ot21_descarte_fusion")[0]

        assert fila["pct_descarte"] == pytest.approx(0.25, abs=1e-4)


@requiere_modelo
class TestPeriodoSinCasos:
    def test_sin_casos_los_porcentajes_son_nulos_y_no_cero(self, particion_limpia):
        """Un período sin casos no tiene una tasa de descarte del 0 %.

        `0 %` afirma que hubo casos y ninguno se descartó — una buena noticia. El
        nulo dice que no hubo nada que medir. Confundirlas presenta un día sin
        actividad como un día impecable.
        """
        filas = ejecutar_informe("ot21_descarte_fusion")

        assert filas == [] or filas[0]["pct_descarte"] is None
