"""Ampliar una dimensión compartida no rompe los hechos que ya la usaban (T043).

`dim_unidad` la usan hoy dos hechos, y mañana más. Si añadirle un atributo
obligara a recargar todos los hechos que la referencian —o peor, si los rompiera
en silencio— el modelo no sería compartible: cada hecho acabaría con su propia
copia de las unidades, y el almacén tendría dos verdades sobre la misma cosa.

La propiedad que lo permite: **los hechos apuntan a la clave de la versión, no a
sus atributos**. Añadir columnas a la dimensión no mueve esas claves.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import contar, requiere_modelo  # noqa: E402

from lib.clickhouse_http_client import execute_clickhouse, query_clickhouse  # noqa: E402

COLUMNA = "atributo_de_prueba"


#: ⚠️ `FINAL` **solo** en los hechos de instantánea acumulada. `hecho_estado_unidad`
#: es de transacción y usa un motor sin deduplicación: pedirle versión final falla
#: con `ILLEGAL_FINAL`. No es una limitación, es la diferencia de diseño — una fila
#: de transacción no se actualiza nunca, así que no hay versiones que reconciliar.
#: (Ocurrió al escribir esta prueba: aplicaba `FINAL` a los tres por costumbre.)
ACUMULADOS = {"hecho_accidente", "hecho_despacho"}


def _atribucion(tabla: str) -> list[dict]:
    final = " FINAL" if tabla in ACUMULADOS else ""
    return query_clickhouse(
        f"SELECT proveedor, count() AS n FROM {tabla}{final} "
        "GROUP BY proveedor ORDER BY proveedor"
    )


@pytest.fixture
def columna_temporal():
    execute_clickhouse(f"ALTER TABLE dim_unidad DROP COLUMN IF EXISTS {COLUMNA}")
    yield
    execute_clickhouse(f"ALTER TABLE dim_unidad DROP COLUMN IF EXISTS {COLUMNA}")


@requiere_modelo
class TestAmpliarDimUnidad:
    def test_la_atribucion_de_los_dos_hechos_no_cambia(self, columna_temporal):
        # Arrange
        despacho_antes = _atribucion("hecho_despacho")
        estado_antes = _atribucion("hecho_estado_unidad")

        # Act
        execute_clickhouse(
            f"ALTER TABLE dim_unidad ADD COLUMN {COLUMNA} Nullable(String)"
        )

        # Assert: los hechos apuntan a la clave de la versión, no a sus atributos
        assert _atribucion("hecho_despacho") == despacho_antes
        assert _atribucion("hecho_estado_unidad") == estado_antes

    def test_las_claves_de_version_siguen_uniendo(self, columna_temporal):
        antes = contar(
            """
            SELECT count() AS n FROM hecho_despacho AS h FINAL
            INNER JOIN dim_unidad AS u FINAL ON h.sk_unidad = u.sk_unidad
            """
        )

        execute_clickhouse(
            f"ALTER TABLE dim_unidad ADD COLUMN {COLUMNA} Nullable(String)"
        )

        assert (
            contar(
                """
                SELECT count() AS n FROM hecho_despacho AS h FINAL
                INNER JOIN dim_unidad AS u FINAL ON h.sk_unidad = u.sk_unidad
                """
            )
            == antes
        )

    def test_el_atributo_nuevo_llega_ausente_a_las_versiones_existentes(self, columna_temporal):
        execute_clickhouse(
            f"ALTER TABLE dim_unidad ADD COLUMN {COLUMNA} Nullable(String)"
        )

        # Mismo criterio que con las métricas: ausente, no cadena vacía. Una
        # cadena vacía es un valor, y aquí no hay valor.
        assert contar(
            f"SELECT count() AS n FROM dim_unidad FINAL WHERE {COLUMNA} IS NOT NULL"
        ) == 0

    def test_el_numero_de_versiones_no_cambia(self, columna_temporal):
        antes = contar("SELECT count() AS n FROM dim_unidad FINAL")

        execute_clickhouse(
            f"ALTER TABLE dim_unidad ADD COLUMN {COLUMNA} Nullable(String)"
        )

        assert contar("SELECT count() AS n FROM dim_unidad FINAL") == antes
