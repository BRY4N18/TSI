"""Recargar un período no duplica (T027, SC-005).

La fase 2 ya probó esto contra un almacén falso. Esta prueba lo comprueba contra
**el almacén de verdad y las tablas de verdad**, que es donde el descarte de
partición puede comportarse distinto de lo que uno cree: sintaxis, particiones
inexistentes, motores con deduplicación en segundo plano.

Escribe en una partición muy posterior a cualquier dato real y la descarta al
terminar, para no alterar las cifras que otras pruebas comprueban.
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
from lib.clickhouse_http_client import execute_clickhouse  # noqa: E402

MARCA = "2099-12-01 00:00:00"


def _filas(cuantas: int) -> list[dict]:
    return [
        {
            "idaccidente": f"PRUEBA-{i:04d}",
            "fecha": FECHA_DE_PRUEBA,
            "fechahora_accidente": MARCA,
            "franja_horaria": "madrugada",
            "fue_descartado": 0,
            "es_duplicado": 0,
            "cargado_en": MARCA,
            "version": MARCA,
        }
        for i in range(cuantas)
    ]


def _en_la_particion() -> int:
    return contar(
        "SELECT count() AS n FROM hecho_accidente "
        f"WHERE toYYYYMM(fecha) = {PARTICION_DE_PRUEBA}"
    )


@pytest.fixture
def particion_limpia():
    execute_clickhouse(f"ALTER TABLE hecho_accidente DROP PARTITION {PARTICION_DE_PRUEBA}")
    yield
    execute_clickhouse(f"ALTER TABLE hecho_accidente DROP PARTITION {PARTICION_DE_PRUEBA}")


@requiere_modelo
class TestRecargaDeUnPeriodo:
    def test_dos_corridas_iguales_dejan_el_mismo_numero_de_filas(self, particion_limpia):
        cargar_particiones("hecho_accidente", _filas(7))
        primera = _en_la_particion()

        cargar_particiones("hecho_accidente", _filas(7))

        assert primera == 7
        assert _en_la_particion() == 7

    def test_una_recarga_con_menos_filas_deja_menos_filas(self, particion_limpia):
        # Si la recarga solo insertara, el período quedaría con las 7 viejas más
        # las 3 nuevas y nadie lo notaría hasta comparar totales
        cargar_particiones("hecho_accidente", _filas(7))
        cargar_particiones("hecho_accidente", _filas(3))

        assert _en_la_particion() == 3

    def test_recargar_no_toca_los_datos_reales(self, particion_limpia):
        antes = contar(
            "SELECT count() AS n FROM hecho_accidente "
            f"WHERE toYYYYMM(fecha) != {PARTICION_DE_PRUEBA}"
        )

        cargar_particiones("hecho_accidente", _filas(5))

        assert (
            contar(
                "SELECT count() AS n FROM hecho_accidente "
                f"WHERE toYYYYMM(fecha) != {PARTICION_DE_PRUEBA}"
            )
            == antes
        )

    def test_descartar_una_particion_inexistente_no_falla(self):
        # La primera corrida de cualquier período se encuentra justo este caso
        execute_clickhouse("ALTER TABLE hecho_accidente DROP PARTITION 190001")
