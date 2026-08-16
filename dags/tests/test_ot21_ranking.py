"""T027 — el ranking de ubicaciones no devuelve coordenadas (FR-015).

La exclusión es **constitucional**: no la levanta ningún cargo, ni siquiera la
autoridad del departamento. Un ranking de puntos negros con latitud y longitud
deja de ser una estadística de tráfico y pasa a ser la ubicación exacta de
sucesos concretos, reidentificables por quien tenga cualquier otra pieza.

El informe da **lugar**, no punto: condado, ciudad y calle. Eso es lo que hace
falta para decidir dónde poner un semáforo, y es todo lo que hace falta.

⚠️ Esta prueba mira el **resultado**, no el texto de la consulta. La del texto ya
existe —`test_catalogo_consultas.py` comprueba que ninguna consulta nombra una
columna de coordenadas— y no basta: una columna llamada `punto` o un `tuple(...)`
pasaría aquella y traería coordenadas igual. Las dos juntas cubren el nombre y el
contenido.
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

COLUMNAS_ESPERADAS = {"condado", "ciudad", "calle", "casos"}


@pytest.fixture
def particion_limpia():
    limpiar_particion()
    yield
    limpiar_particion()


@requiere_modelo
class TestSinCoordenadas:
    def test_el_ranking_solo_devuelve_lugar_y_conteo(self, particion_limpia):
        cargar_casos([caso("T027-a"), caso("T027-b")])

        filas = ejecutar_informe("ot21_ranking_ubicaciones", top=10)

        assert set(filas[0]) == COLUMNAS_ESPERADAS, (
            f"el ranking devuelve columnas no previstas: "
            f"{set(filas[0]) - COLUMNAS_ESPERADAS}"
        )

    def test_ningun_valor_devuelto_parece_una_coordenada(self, particion_limpia):
        # Comprobar los nombres no basta: una columna podría llamarse `zona` y
        # traer un par de grados. Esto mira lo que sale.
        cargar_casos([caso("T027-a")])

        for fila in ejecutar_informe("ot21_ranking_ubicaciones", top=10):
            for clave, valor in fila.items():
                if clave == "casos":
                    continue
                assert not _parece_coordenada(valor), (
                    f"'{clave}' devuelve algo con forma de coordenada: {valor!r}"
                )


@requiere_modelo
class TestElTope:
    def test_el_tope_limita_las_filas_devueltas(self, particion_limpia):
        cargar_casos([
            caso(f"T027-{i}", idcalle=i, condado=f"Zona {i}") for i in range(1, 6)
        ])

        assert len(ejecutar_informe("ot21_ranking_ubicaciones", top=3)) == 3

    def test_el_orden_es_por_casos_descendente(self, particion_limpia):
        cargar_casos(
            [caso(f"T027-mucho-{i}", condado="Zona alta", idcalle=1) for i in range(3)]
            + [caso("T027-poco", condado="Zona baja", idcalle=2)]
        )

        filas = ejecutar_informe("ot21_ranking_ubicaciones", top=10)

        assert [f["casos"] for f in filas] == sorted(
            (f["casos"] for f in filas), reverse=True
        )
        assert filas[0]["condado"] == "Zona alta"


@requiere_modelo
class TestUbicacionNoResoluble:
    def test_una_calle_fuera_del_catalogo_sale_como_desconocido(self, particion_limpia):
        """No desaparece del ranking, y tampoco inventa un nombre.

        El caso ocurrió y cuenta para el conteo de su zona; lo que no se sabe es
        el nombre de la calle. Dejarlo fuera restaría casos del ranking sin que
        nada lo indicara — el mismo fallo que T025 vigila en las distribuciones.
        """
        cargar_casos([caso("T027-huerfana", idcalle=999999)])

        filas = ejecutar_informe("ot21_ranking_ubicaciones", top=10)

        assert len(filas) == 1
        assert filas[0]["calle"] == "Desconocido"
        assert filas[0]["casos"] == 1


def _parece_coordenada(valor) -> bool:
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        return -180.0 <= float(valor) <= 180.0 and float(valor) != int(float(valor))
    if isinstance(valor, (list, tuple)):
        return len(valor) == 2 and all(isinstance(v, (int, float)) for v in valor)
    return False
