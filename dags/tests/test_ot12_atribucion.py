"""T039 — el pasado de la unidad no se reescribe (SC-004).

Si un proveedor cambia de nombre, o una unidad pasa de uno a otro, **las bajas ya
ocurridas conservan el proveedor de entonces**. Un proveedor que hereda las
unidades de otro no debe heredar también sus bajas forzadas, y uno que se marcha
no debe llevárselas.

Sobre este informe se decide con quién se sigue trabajando, así que la atribución
no es un detalle de implementación.

`hecho_baja_unidad` guarda el proveedor **resuelto en la carga** por atribución
histórica. Esta prueba comprueba que esa decisión sobrevive: cambiar la unidad en
la dimensión no toca los hechos ya cargados.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    FECHA_DE_PRUEBA,
    PARTICION_DE_PRUEBA,
    ejecutar_red_operativa,
    requiere_modelo,
)

from lib.clickhouse_http_client import execute_clickhouse  # noqa: E402

UNIDAD = 9701
ENTONCES = "Proveedor de entonces"
AHORA = "Proveedor de ahora"


def _baja(idbaja: int, proveedor: str) -> dict:
    return {
        "idbaja": idbaja,
        "fecha": FECHA_DE_PRUEBA,
        "fechahora": f"{FECHA_DE_PRUEBA} 12:00:00",
        "sk_unidad": 970000,
        "idunidademergencia": UNIDAD,
        "unidad": "ATR-1",
        # El proveedor **del momento de la baja**, no el de hoy.
        "proveedor": proveedor,
        "tipo_baja": "Forzada",
        "motivo": "prueba de atribucion",
        "con_caso_en_curso": 0,
        "dias_en_flota": 10,
        "cargado_en": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


def _version(sk: int, proveedor: str, *, vigente: int) -> dict:
    return {
        "sk_unidad": sk,
        "idunidademergencia": UNIDAD,
        "placa": "ATR-1",
        "idcliente": 1,
        "proveedor": proveedor,
        "idcondado": 1,
        "condado": "X",
        "fecha_alta": None,
        "tuvo_primer_acceso": 1,
        "valido_desde": "1970-01-01 00:00:00" if vigente == 0 else "2026-09-01 00:00:00",
        "valido_hasta": "2026-09-01 00:00:00" if vigente == 0 else None,
        "es_vigente": vigente,
        "inicio_es_real": 0,
        "version": f"{FECHA_DE_PRUEBA} 12:00:00",
    }


def _insertar(tabla: str, filas: list[dict]) -> None:
    payload = "\n".join(json.dumps(f, ensure_ascii=False) for f in filas)
    execute_clickhouse(f"INSERT INTO {tabla} FORMAT JSONEachRow\n{payload}")


@pytest.fixture
def escenario():
    def limpiar():
        execute_clickhouse(
            f"ALTER TABLE hecho_baja_unidad DROP PARTITION {PARTICION_DE_PRUEBA}"
        )
        execute_clickhouse(
            f"ALTER TABLE dim_unidad DELETE WHERE idunidademergencia = {UNIDAD} "
            f"SETTINGS mutations_sync = 2"
        )
    limpiar()
    _insertar("dim_unidad", [_version(970001, ENTONCES, vigente=1)])
    _insertar("hecho_baja_unidad", [_baja(1, ENTONCES)])
    yield
    limpiar()


def _bajas_de(proveedor: str) -> int:
    return sum(
        f["bajas"] for f in ejecutar_red_operativa("ot12_bajas_forzadas")
        if f["proveedor"] == proveedor and f["motivo"] == "prueba de atribucion"
    )


@requiere_modelo
class TestElPasadoDeLaUnidadNoSeReescribe:
    def test_cambiar_el_proveedor_no_mueve_las_bajas_anteriores(self, escenario):
        """⚠️ Quien hereda las unidades no hereda las bajas forzadas de quien se fue."""
        antes = _bajas_de(ENTONCES)
        assert antes == 1, "el escenario no se cargó"

        # La unidad cambia de proveedor: versión cerrada + versión nueva.
        _insertar("dim_unidad", [
            _version(970001, ENTONCES, vigente=0),
            _version(970002, AHORA, vigente=1),
        ])

        assert _bajas_de(ENTONCES) == 1, (
            "la baja se reatribuyó al proveedor actual: el informe está "
            "resolviendo el proveedor al consultar en vez de leerlo del hecho"
        )
        assert _bajas_de(AHORA) == 0, (
            "el proveedor nuevo heredó una baja que no es suya"
        )

    def test_el_hecho_conserva_el_proveedor_del_momento(self, escenario):
        # La comprobación directa de la decisión de diseño: si el hecho no lo
        # guardara, la prueba anterior no podría pasar.
        _insertar("dim_unidad", [
            _version(970001, ENTONCES, vigente=0),
            _version(970002, AHORA, vigente=1),
        ])

        filas = [
            f for f in ejecutar_red_operativa("ot12_rotacion_flota")
            if f["proveedor"] == ENTONCES
        ]

        assert filas and filas[0]["bajas"] >= 1
