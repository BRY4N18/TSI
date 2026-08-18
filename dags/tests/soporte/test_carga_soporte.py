"""T032, T033 — recargar el mismo día no duplica; las fechas sintéticas no tocan lo real."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from lib.carga_particion import cargar_particiones, particion_de  # noqa: E402
from tests.almacen import FECHA_DE_PRUEBA, PARTICION_DE_PRUEBA  # noqa: E402

AHORA = datetime(2026, 8, 17, 12, 0, 0)


class AlmacenFalso:
    def __init__(self):
        self.sql: list[str] = []
        self.insertados: dict[str, list] = {}

    def ejecutar(self, sql: str) -> None:
        self.sql.append(sql)

    def insertar(self, tabla: str, filas: list) -> None:
        self.insertados.setdefault(tabla, []).append(filas)


def test_ejecutar_dos_veces_no_altera_los_recuentos():
    almacen = AlmacenFalso()
    filas = [{"fecha": FECHA_DE_PRUEBA, "id_reclamo": 1}]
    cargar_particiones(
        "hecho_ticket", filas,
        ejecutar=almacen.ejecutar, insertar=almacen.insertar,
    )
    cargar_particiones(
        "hecho_ticket", filas,
        ejecutar=almacen.ejecutar, insertar=almacen.insertar,
    )
    assert almacen.sql.count(f"ALTER TABLE hecho_ticket DROP PARTITION {PARTICION_DE_PRUEBA}") == 2
    assert len(almacen.insertados["hecho_ticket"][0]) == len(almacen.insertados["hecho_ticket"][1])


def test_las_fechas_sinteticas_caen_en_la_particion_de_prueba():
    assert particion_de(FECHA_DE_PRUEBA) == PARTICION_DE_PRUEBA
    assert PARTICION_DE_PRUEBA == 209912
    assert particion_de("2026-08-17") != PARTICION_DE_PRUEBA
