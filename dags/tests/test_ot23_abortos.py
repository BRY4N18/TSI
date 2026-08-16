"""T045 — los cinco desenlaces se distinguen.

`abortado` no es `rechazado`, ni `vencido`, ni `en_curso`. Los cuatro suenan a
«no salió bien» y significan cosas distintas, con responsables distintos:

* **rechazado** — alguien vio el aviso y dijo que no.
* **vencido**   — nadie contestó. No hubo decisión que discutir.
* **abortado**  — se aceptó y luego se canceló. Había un compromiso y se rompió.
* **en_curso**  — todavía no ha terminado. **No es un fracaso.**

Agruparlos en un «no atendidos» produce un porcentaje que no dice qué arreglar; y
meter `en_curso` en el saco convierte cada consulta hecha a media tarde en un
informe pesimista que mejora solo al día siguiente.
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

DESENLACES = ("confirmado", "rechazado", "vencido", "abortado", "en_curso")


@pytest.fixture
def sin_despachos():
    limpiar_despachos()
    yield
    limpiar_despachos()


def _informe() -> dict:
    filas = ejecutar_informe("ot23_abortos_perdidas")
    return filas[0] if filas else {}


@requiere_modelo
class TestLosCincoDesenlaces:
    def test_uno_de_cada_cuenta_en_su_columna_y_solo_en_la_suya(self, sin_despachos):
        cargar_despachos([
            despacho(i + 1, idaccidente=f"C{i}", resultado=r,
                     segundos_transito=400 if r == "confirmado" else None)
            for i, r in enumerate(DESENLACES)
        ])

        informe = _informe()

        assert informe["despachos"] == 5
        for desenlace in DESENLACES:
            columna = "en_curso" if desenlace == "en_curso" else f"{desenlace}s"
            assert informe[columna] == 1, f"'{desenlace}' no cuenta en su columna"

    def test_las_cinco_columnas_suman_el_total(self, sin_despachos):
        # Si un desenlace nuevo apareciera en el origen sin columna aquí, las
        # cifras seguirían siendo plausibles y el informe dejaría de cuadrar sin
        # que nada lo dijera.
        cargar_despachos([
            despacho(i + 1, idaccidente=f"C{i}", resultado=r,
                     segundos_transito=400 if r == "confirmado" else None)
            for i, r in enumerate(DESENLACES)
        ])

        informe = _informe()
        suma = sum(
            informe["en_curso" if d == "en_curso" else f"{d}s"] for d in DESENLACES
        )

        assert suma == informe["despachos"]

    def test_un_abortado_no_cuenta_como_rechazado_ni_como_vencido(self, sin_despachos):
        cargar_despachos([
            despacho(1, idaccidente="A", resultado="abortado", segundos_transito=None)
        ])

        informe = _informe()

        assert informe["abortados"] == 1
        assert informe["rechazados"] == 0
        assert informe["vencidos"] == 0

    def test_un_desenlace_sin_casos_sale_como_cero_y_no_desaparece(self, sin_despachos):
        """Un cero que falta se lee como un dato que no existe.

        Agrupar por `resultado` habría hecho desaparecer de la respuesta los
        desenlaces sin ningún caso en el período. En una pantalla eso es la
        diferencia entre «no hubo ningún aborto» —una buena noticia— y «no
        sabemos cuántos abortos hubo».
        """
        cargar_despachos([despacho(1, idaccidente="A", resultado="confirmado")])

        informe = _informe()

        for columna in ("rechazados", "vencidos", "abortados", "en_curso"):
            assert informe[columna] == 0, f"'{columna}' desapareció en vez de valer 0"

    def test_en_curso_no_cuenta_como_aborto(self, sin_despachos):
        cargar_despachos([
            despacho(1, idaccidente="A", resultado="confirmado"),
            despacho(2, idaccidente="B", resultado="en_curso", segundos_transito=None),
        ])

        informe = _informe()

        assert informe["en_curso"] == 1
        assert informe["abortados"] == 0
        assert informe["pct_aborto"] == 0.0
