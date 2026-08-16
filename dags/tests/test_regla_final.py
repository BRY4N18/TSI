"""Por qué la Regla 2 del contrato de consumo existe (T051).

La regla dice: **toda consulta sobre un hecho de instantánea acumulada o sobre
una dimensión debe forzar la versión final**. Suena a formalismo hasta que se ve
lo que pasa al omitirla.

El motor con deduplicación **no deduplica al escribir**: guarda ambas versiones y
las fusiona en segundo plano, cuando le viene bien. Entre la escritura y la
fusión, una consulta sin `FINAL` devuelve **las dos**. Es decir: la cifra sale
inflada **de forma intermitente**, y deja de estarlo sola al cabo de un rato.

Es el peor fallo posible en un informe, porque no es reproducible: quien lo
reporte verá cifras normales al comprobarlo.

Esta prueba lo produce a propósito, en una partición de prueba.
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

from lib.clickhouse_http_client import execute_clickhouse, insert_rows  # noqa: E402
from lib.tipos_almacen import ajustar_tipos  # noqa: E402


def _fila(version: str):
    return {
        "idaccidente": "PRUEBA-FINAL",
        "fecha": FECHA_DE_PRUEBA,
        "fechahora_accidente": "2099-12-01 00:00:00",
        "franja_horaria": "madrugada",
        "fue_descartado": 0,
        "es_duplicado": 0,
        "cargado_en": version,
        "version": version,
    }


def _en_particion(final: bool) -> int:
    modificador = " FINAL" if final else ""
    return contar(
        f"SELECT count() AS n FROM hecho_accidente{modificador} "
        f"WHERE toYYYYMM(fecha) = {PARTICION_DE_PRUEBA}"
    )


@pytest.fixture
def particion_limpia():
    execute_clickhouse(f"ALTER TABLE hecho_accidente DROP PARTITION {PARTICION_DE_PRUEBA}")
    yield
    execute_clickhouse(f"ALTER TABLE hecho_accidente DROP PARTITION {PARTICION_DE_PRUEBA}")


@requiere_modelo
class TestOmitirElForzadoDeVersion:
    def test_produce_filas_duplicadas(self, particion_limpia):
        # Arrange: el mismo caso escrito dos veces, como haría una recarga que
        # actualiza un hito. Se insertan por separado para que queden en partes
        # distintas y la fusión no las junte todavía.
        insert_rows("hecho_accidente", ajustar_tipos("hecho_accidente", [_fila("2099-12-01 00:00:00")]))
        insert_rows("hecho_accidente", ajustar_tipos("hecho_accidente", [_fila("2099-12-02 00:00:00")]))

        # Assert: ⚠️ sin `FINAL`, un caso cuenta como dos
        assert _en_particion(final=False) == 2
        assert _en_particion(final=True) == 1

    def test_la_version_que_gana_es_la_ultima(self, particion_limpia):
        insert_rows("hecho_accidente", ajustar_tipos("hecho_accidente", [_fila("2099-12-01 00:00:00")]))
        insert_rows("hecho_accidente", ajustar_tipos("hecho_accidente", [_fila("2099-12-02 00:00:00")]))

        from lib.clickhouse_http_client import query_clickhouse

        fila = query_clickhouse(
            "SELECT cargado_en FROM hecho_accidente FINAL "
            f"WHERE toYYYYMM(fecha) = {PARTICION_DE_PRUEBA}"
        )[0]
        assert fila["cargado_en"] == "2099-12-02 00:00:00"

    def test_el_hecho_de_transaccion_no_tiene_este_problema(self):
        # Y por eso la regla NO se le aplica: su motor no deduplica porque no hay
        # nada que deduplicar. Pedirle `FINAL` es un error, no una precaución.
        from lib.clickhouse_http_client import query_clickhouse

        with pytest.raises(RuntimeError, match="ILLEGAL_FINAL"):
            query_clickhouse("SELECT count() FROM hecho_ping_unidad FINAL")
