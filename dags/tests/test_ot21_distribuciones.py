"""T025 — ningún caso se pierde al clasificar (SC-007).

Un reparto que descarta lo que no sabe clasificar es indetectable desde el propio
informe: los porcentajes siguen sumando 100 % **entre ellos**, y las categorías
que se ven siguen teniendo cifras plausibles. Lo único que cambia es el total, y
el total no aparece en el gráfico.

Por eso lo que se comprueba aquí no es que los porcentajes sumen uno, sino que la
suma de los **casos** de todas las categorías es igual al total del período.
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
class TestDistribucionPorSeveridad:
    def test_la_suma_de_las_categorias_es_el_total_del_periodo(self, particion_limpia):
        cargar_casos([
            caso("T025-a"),
            caso("T025-b"),
            caso("T025-sin-severidad", severidad=False),
        ])

        filas = ejecutar_informe("ot21_distribucion_severidad")

        assert sum(f["casos"] for f in filas) == 3, (
            "el reparto no suma el total del período: hay casos que se perdieron "
            "al clasificar, y los porcentajes seguirían sumando 100 % entre ellos"
        )

    def test_un_caso_sin_severidad_aparece_bajo_desconocido(self, particion_limpia):
        cargar_casos([caso("T025-a"), caso("T025-sin", severidad=False)])

        filas = ejecutar_informe("ot21_distribucion_severidad")
        por_categoria = {f["severidad"]: f["casos"] for f in filas}

        assert por_categoria.get("Desconocido") == 1, (
            "el caso sin severidad no aparece: filtrarlo daría un reparto que "
            "suma menos que el período sin que nada lo delate"
        )

    def test_los_porcentajes_se_calculan_sobre_el_total_y_no_sobre_los_clasificados(
        self, particion_limpia
    ):
        # La diferencia solo se ve cuando hay casos sin clasificar: con tres
        # casos, uno de ellos sin severidad, la categoría 'Leve' es 2/3 y no 2/2.
        cargar_casos([
            caso("T025-a"),
            caso("T025-b"),
            caso("T025-sin", severidad=False),
        ])

        filas = ejecutar_informe("ot21_distribucion_severidad")
        leve = next(f for f in filas if f["severidad"] == "Leve")

        assert leve["pct"] == pytest.approx(2 / 3, abs=1e-4)


@requiere_modelo
class TestDistribucionPorZona:
    def test_la_suma_de_las_zonas_es_el_total_del_periodo(self, particion_limpia):
        cargar_casos([
            caso("T025-z1", condado="Cuauhtemoc"),
            caso("T025-z2", condado="Benito Juarez"),
            caso("T025-z3", ubicacion=False),
        ])

        filas = ejecutar_informe("ot21_distribucion_zona")

        assert sum(f["casos"] for f in filas) == 3

    def test_un_caso_sin_zona_aparece_bajo_desconocido(self, particion_limpia):
        cargar_casos([caso("T025-z1"), caso("T025-sin-zona", ubicacion=False)])

        filas = ejecutar_informe("ot21_distribucion_zona")
        por_zona = {f["condado"]: f["casos"] for f in filas}

        assert por_zona.get("Desconocido") == 1


@requiere_modelo
class TestPeriodoSinCasos:
    def test_un_periodo_vacio_no_devuelve_una_fila_de_ceros(self, particion_limpia):
        """El contrato lo pide: `data: []`, que es distinto de una fila a cero.

        Una fila con `casos: 0` afirma que se midió y no hubo nada. Una lista
        vacía dice que no hay nada que repartir. En un gráfico la primera pinta
        una barra a cero —una categoría que existe y está vacía— y la segunda no
        pinta nada, que es lo correcto.
        """
        assert ejecutar_informe("ot21_distribucion_severidad") == []
        assert ejecutar_informe("ot21_distribucion_zona") == []
