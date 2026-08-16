"""T046 — el pasado no se reescribe (SC-003).

Si un proveedor cambia de nombre, o una unidad pasa de un proveedor a otro, las
cifras de los meses ya cerrados **no pueden moverse**. El trabajo lo hizo quien lo
hizo, y atribuirlo al dueño actual reescribe la historia.

Importa más de lo que parece porque sobre estas cifras se decide qué proveedor
sigue: un proveedor que hereda las unidades de otro heredaría también sus
rechazos, y uno que se marcha se llevaría los suyos.

`hecho_despacho` guarda el proveedor **en el momento del despacho** —atribución
histórica— en vez de resolverlo contra la dimensión al consultar. Esta prueba
comprueba que esa decisión sobrevive: cambiar la unidad en la dimensión no toca
los hechos ya cargados.
"""

from __future__ import annotations

import json
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

from lib.clickhouse_http_client import execute_clickhouse  # noqa: E402

UNIDAD = "T046-UNI"
ID_UNIDAD = 990046
PROVEEDOR_ENTONCES = "Proveedor de entonces"
PROVEEDOR_AHORA = "Proveedor de ahora"


def _version_de_unidad(proveedor: str, *, version: str, es_vigente: int = 1) -> dict:
    return {
        "sk_unidad": 99000046,
        "idunidademergencia": ID_UNIDAD,
        "placa": UNIDAD,
        "nombre_unidad": "Unidad de prueba T046",
        "idcliente": 1,
        "proveedor": proveedor,
        "condado": "Cuauhtemoc",
        "valido_desde": "2099-01-01 00:00:00",
        "valido_hasta": None,
        "es_vigente": es_vigente,
        "inicio_es_real": 1,
        "version": version,
    }


def _cargar_unidad(fila: dict) -> None:
    execute_clickhouse(f"INSERT INTO dim_unidad FORMAT JSONEachRow\n{json.dumps(fila)}")


def _limpiar_unidad() -> None:
    execute_clickhouse(
        f"ALTER TABLE dim_unidad DELETE WHERE idunidademergencia = {ID_UNIDAD} "
        f"SETTINGS mutations_sync = 2"
    )


@pytest.fixture
def escenario():
    limpiar_despachos()
    _limpiar_unidad()
    _cargar_unidad(_version_de_unidad(PROVEEDOR_ENTONCES, version="2099-01-01 00:00:00"))
    cargar_despachos([
        despacho(1, idaccidente="T046-a", unidad=UNIDAD, proveedor=PROVEEDOR_ENTONCES),
        despacho(2, idaccidente="T046-b", unidad=UNIDAD, proveedor=PROVEEDOR_ENTONCES,
                 resultado="rechazado", segundos_transito=None),
        despacho(3, idaccidente="T046-c", unidad=UNIDAD, proveedor=PROVEEDOR_ENTONCES,
                 resultado="vencido", segundos_transito=None),
    ])
    yield
    limpiar_despachos()
    _limpiar_unidad()


def _fila(informe: str) -> dict:
    propias = [f for f in ejecutar_informe(informe) if f.get("unidad") == UNIDAD]
    return propias[0] if propias else {}


@requiere_modelo
class TestElPasadoNoSeReescribe:
    def test_cambiar_el_proveedor_no_mueve_la_carga_de_un_periodo_anterior(self, escenario):
        antes = _fila("ot22_carga_por_unidad")

        _cargar_unidad(_version_de_unidad(PROVEEDOR_AHORA, version="2100-01-01 00:00:00"))

        despues = _fila("ot22_carga_por_unidad")

        assert despues == antes, (
            "las cifras del período cambiaron al cambiar el proveedor en la "
            "dimensión: el informe está resolviendo la atribución al consultar"
        )

    def test_los_rechazos_siguen_atribuidos_a_quien_los_hizo(self, escenario):
        antes = _fila("ot22_rechazo_timeout_por_unidad")

        _cargar_unidad(_version_de_unidad(PROVEEDOR_AHORA, version="2100-01-01 00:00:00"))

        despues = _fila("ot22_rechazo_timeout_por_unidad")

        assert despues["proveedor"] == PROVEEDOR_ENTONCES, (
            "los rechazos se reatribuyeron al proveedor actual: quien hereda las "
            "unidades heredaría también los rechazos de quien se marchó"
        )
        assert despues["rechazados"] == antes["rechazados"] == 1
        assert despues["vencidos"] == antes["vencidos"] == 1

    def test_el_hecho_conserva_el_proveedor_del_momento_del_despacho(self, escenario):
        # La comprobación directa de la decisión de diseño: si el hecho no
        # guardara el proveedor, las dos pruebas anteriores no podrían pasar.
        _cargar_unidad(_version_de_unidad(PROVEEDOR_AHORA, version="2100-01-01 00:00:00"))

        assert _fila("ot22_carga_por_unidad")["proveedor"] == PROVEEDOR_ENTONCES
