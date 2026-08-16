"""T044 — el primer intento se cuenta bien.

Un caso con dos rechazos y una confirmación **no** se resolvió al primer intento.
Parece obvio dicho así, y es exactamente lo que el informe anterior no podía ver:
con grano de caso solo queda el despacho que acabó confirmado, y los dos rechazos
no existen en ninguna tabla. El indicador daría 100 % justo en el caso que peor
fue.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    cargar_despachos,
    despacho,
    ejecutar_informe,
    limpiar_despachos,
    requiere_modelo,
)


@pytest.fixture
def sin_despachos():
    limpiar_despachos()
    yield
    limpiar_despachos()


def _indicador() -> dict:
    filas = ejecutar_informe("ot22_primer_intento")
    return filas[0] if filas else {}


@requiere_modelo
class TestElPrimerIntento:
    def test_un_caso_con_dos_rechazos_y_una_confirmacion_no_cuenta_como_resuelto(
        self, sin_despachos
    ):
        cargar_despachos([
            despacho(1, idaccidente="A", numero_intento=1, resultado="rechazado",
                     segundos_transito=None),
            despacho(2, idaccidente="A", numero_intento=2, resultado="rechazado",
                     segundos_transito=None),
            despacho(3, idaccidente="A", numero_intento=3, resultado="confirmado"),
        ])

        indicador = _indicador()

        assert indicador["casos"] == 1, "el denominador cuenta casos, no intentos"
        assert indicador["resueltos_primer_intento"] == 0, (
            "el caso se dio por resuelto al primer intento: los dos rechazos "
            "previos desaparecieron de la cuenta"
        )
        assert indicador["pct_primer_intento"] == 0.0

    def test_un_caso_confirmado_a_la_primera_si_cuenta(self, sin_despachos):
        cargar_despachos([despacho(1, idaccidente="B", numero_intento=1, resultado="confirmado")])

        assert _indicador()["pct_primer_intento"] == 1.0

    def test_el_denominador_no_cuenta_los_intentos_posteriores(self, sin_despachos):
        # Un caso con tres intentos aporta **uno** al denominador, no tres. Si
        # contara tres, un solo caso problemático hundiría el indicador tanto
        # como tres casos distintos que fallaron a la primera.
        cargar_despachos([
            despacho(1, idaccidente="A", numero_intento=1, resultado="rechazado",
                     segundos_transito=None),
            despacho(2, idaccidente="A", numero_intento=2, resultado="rechazado",
                     segundos_transito=None),
            despacho(3, idaccidente="A", numero_intento=3, resultado="confirmado"),
            despacho(4, idaccidente="B", numero_intento=1, resultado="confirmado"),
        ])

        indicador = _indicador()

        assert indicador["casos"] == 2
        assert indicador["resueltos_primer_intento"] == 1
        assert indicador["pct_primer_intento"] == 0.5

    def test_un_primer_intento_en_curso_cuenta_en_el_denominador(self, sin_despachos):
        # Todavía no se ha resuelto al primer intento. Excluirlo mejoraría el
        # indicador por el simple hecho de tener casos sin terminar, que es una
        # forma de que el número suba cuando las cosas van peor.
        cargar_despachos([
            despacho(1, idaccidente="A", numero_intento=1, resultado="confirmado"),
            despacho(2, idaccidente="B", numero_intento=1, resultado="en_curso",
                     segundos_transito=None),
        ])

        indicador = _indicador()

        assert indicador["casos"] == 2
        assert indicador["pct_primer_intento"] == 0.5

    def test_publica_la_meta_del_cuadro_de_mando(self, sin_despachos):
        cargar_despachos([despacho(1, idaccidente="A")])

        assert _indicador()["meta"] == 0.9
