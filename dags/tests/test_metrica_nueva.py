"""Una métrica añadida se presenta **ausente** en las filas anteriores (T042, FR-018).

Es el caso que más silenciosamente corrompe un almacén que crece. Se añade una
métrica hoy; las filas de los seis meses anteriores no la tienen. Si el almacén
la rellena con `0`:

- un promedio la incluye y **se hunde**, sin que nadie sepa por qué;
- una suma la incluye y no cambia, así que el error pasa desapercibido más tiempo;
- un informe muestra «0» donde debería mostrar «sin dato», que son cosas
  distintas: cero heridos es una medición, «no lo medíamos» no lo es.

Con la métrica ausente, el promedio la excluye y el informe puede decir desde qué
fecha existe el dato.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    FECHA_DE_PRUEBA,
    PARTICION_DE_PRUEBA,
    contar,
    requiere_modelo,
)

from lib.carga_particion import cargar_particiones  # noqa: E402
from lib.clickhouse_http_client import execute_clickhouse, query_clickhouse  # noqa: E402

MARCA = "2099-12-01 00:00:00"
COLUMNA = "metrica_de_prueba"


def _fila(idaccidente, **extra):
    fila = {
        "idaccidente": idaccidente,
        "fecha": FECHA_DE_PRUEBA,
        "fechahora_accidente": MARCA,
        "franja_horaria": "madrugada",
        "fue_descartado": 0,
        "es_duplicado": 0,
        "cargado_en": MARCA,
        "version": MARCA,
    }
    fila.update(extra)
    return fila


@pytest.fixture
def columna_temporal():
    def limpiar():
        execute_clickhouse(f"ALTER TABLE hecho_accidente DROP PARTITION {PARTICION_DE_PRUEBA}")
        execute_clickhouse(f"ALTER TABLE hecho_accidente DROP COLUMN IF EXISTS {COLUMNA}")

    limpiar()
    yield
    limpiar()


@requiere_modelo
class TestMetricaAnadidaDespues:
    def test_las_filas_anteriores_la_tienen_ausente_y_no_en_cero(self, columna_temporal):
        # Arrange: filas cargadas ANTES de que la métrica existiera
        cargar_particiones("hecho_accidente", [_fila("PRUEBA-VIEJA-1"), _fila("PRUEBA-VIEJA-2")])

        # Act: se añade la métrica
        execute_clickhouse(
            f"ALTER TABLE hecho_accidente ADD COLUMN {COLUMNA} Nullable(Int32)"
        )

        # Assert: ⚠️ ausente, no cero
        assert (
            contar(
                f"SELECT count() AS n FROM hecho_accidente "
                f"WHERE toYYYYMM(fecha) = {PARTICION_DE_PRUEBA} AND {COLUMNA} IS NULL"
            )
            == 2
        )
        assert (
            contar(
                f"SELECT count() AS n FROM hecho_accidente "
                f"WHERE toYYYYMM(fecha) = {PARTICION_DE_PRUEBA} AND {COLUMNA} = 0"
            )
            == 0
        )

    def test_el_promedio_excluye_las_filas_sin_el_dato(self, columna_temporal):
        # Arrange: dos filas viejas sin la métrica y una nueva con valor 10
        cargar_particiones("hecho_accidente", [_fila("PRUEBA-VIEJA-1"), _fila("PRUEBA-VIEJA-2")])
        execute_clickhouse(
            f"ALTER TABLE hecho_accidente ADD COLUMN {COLUMNA} Nullable(Int32)"
        )
        from lib.clickhouse_http_client import insert_rows
        from lib.tipos_almacen import _CACHE, ajustar_tipos

        _CACHE.pop("hecho_accidente", None)  # la tabla acaba de cambiar de forma
        insert_rows(
            "hecho_accidente",
            ajustar_tipos("hecho_accidente", [_fila("PRUEBA-NUEVA", **{COLUMNA: 10})]),
        )

        # Act
        media = query_clickhouse(
            f"SELECT avg({COLUMNA}) AS media FROM hecho_accidente "
            f"WHERE toYYYYMM(fecha) = {PARTICION_DE_PRUEBA}"
        )[0]["media"]

        # Assert: 10, no 3.33 — que es lo que daría si las ausentes contaran cero
        assert float(media) == 10.0

    def test_la_columna_nueva_no_altera_las_filas_de_otros_periodos(self, columna_temporal):
        antes = contar(
            "SELECT count() AS n FROM hecho_accidente FINAL "
            f"WHERE toYYYYMM(fecha) != {PARTICION_DE_PRUEBA}"
        )

        execute_clickhouse(
            f"ALTER TABLE hecho_accidente ADD COLUMN {COLUMNA} Nullable(Int32)"
        )

        assert (
            contar(
                "SELECT count() AS n FROM hecho_accidente FINAL "
                f"WHERE toYYYYMM(fecha) != {PARTICION_DE_PRUEBA}"
            )
            == antes
        )
