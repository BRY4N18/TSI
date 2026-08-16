"""T041 — la capacidad es la del período, no la de hoy (FR-006).

El endpoint anterior cuenta la flota con `activo = true`. Aplicado a un período
pasado, eso responde a una pregunta que nadie hizo: «¿cuántos casos hubo entonces
por cada unidad que tenemos **ahora**?».

El síntoma es el peor posible: **el histórico se reescribe solo**. El informe de
marzo consultado en marzo y el mismo informe de marzo consultado en agosto dan
cifras distintas, sin que en marzo haya pasado nada. Nada falla, nada avisa, y
las dos cifras son plausibles.

Esta prueba lo reproduce: da de baja una unidad **después** del período medido y
comprueba que ese período no se mueve.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    FECHA_DE_PRUEBA,
    cargar_despachos,
    despacho,
    ejecutar_informe,
    limpiar_despachos,
    requiere_modelo,
)

from lib.clickhouse_http_client import execute_clickhouse  # noqa: E402

#: Condado propio de la prueba. Sin él, las 19 unidades reales —todas vigentes y
#: sin fecha de fin— también contarían para el mes de prueba y la cifra medida no
#: sería atribuible a la unidad que esta prueba manipula.
CONDADO = "Condado de prueba T041"
ID_UNIDAD = 990041


def _version_de_unidad(*, valido_hasta: str | None, es_vigente: int, version: str) -> dict:
    return {
        "sk_unidad": 99000041,
        "idunidademergencia": ID_UNIDAD,
        "placa": "T041-AAA",
        "nombre_unidad": "Unidad de prueba T041",
        "idcliente": 1,
        "proveedor": "Proveedor de prueba",
        "condado": CONDADO,
        "valido_desde": "2099-01-01 00:00:00",
        "valido_hasta": valido_hasta,
        "es_vigente": es_vigente,
        "inicio_es_real": 1,
        "version": version,
    }


def _cargar_unidad(fila: dict) -> None:
    execute_clickhouse(f"INSERT INTO dim_unidad FORMAT JSONEachRow\n{json.dumps(fila)}")


def _limpiar_unidad() -> None:
    # `dim_unidad` no está particionada, así que la limpieza es por filtro. Se
    # borra por `idunidademergencia`, que es propio de esta prueba.
    execute_clickhouse(
        f"ALTER TABLE dim_unidad DELETE WHERE idunidademergencia = {ID_UNIDAD} "
        f"SETTINGS mutations_sync = 2"
    )


@pytest.fixture
def escenario():
    limpiar_despachos()
    _limpiar_unidad()
    # Una unidad vigente desde 2099-01, sin fecha de fin.
    _cargar_unidad(
        _version_de_unidad(valido_hasta=None, es_vigente=1, version="2099-01-01 00:00:00")
    )
    # Cuatro casos en el mes medido, en el condado de la prueba.
    cargar_despachos([
        despacho(i, idaccidente=f"T041-{i}", condado=CONDADO) for i in range(1, 5)
    ])
    yield
    limpiar_despachos()
    _limpiar_unidad()


def _fila_del_condado() -> dict:
    filas = ejecutar_informe("ot22_ratio_demanda_capacidad")
    propias = [f for f in filas if f["condado"] == CONDADO]
    return propias[0] if propias else {}


@requiere_modelo
class TestLaCapacidadEsLaDelPeriodo:
    def test_cuenta_la_unidad_vigente_durante_el_periodo(self, escenario):
        fila = _fila_del_condado()

        assert fila["casos"] == 4
        assert fila["unidades_vigentes"] == 1
        assert fila["ratio"] == 4.0

    def test_dar_de_baja_la_unidad_despues_no_cambia_el_periodo_anterior(self, escenario):
        """⚠️ La prueba que da nombre al módulo en este informe.

        La unidad se retira con efecto **posterior** al mes medido. Ese mes no
        puede moverse: entonces la unidad existía y estaba disponible.

        Una implementación con `es_vigente = 1` devolvería aquí `0` unidades y un
        ratio nulo — y lo haría en silencio, cambiando un informe ya publicado.
        """
        antes = _fila_del_condado()

        # Baja con efecto en 2100-03, es decir **después** del mes medido.
        _cargar_unidad(
            _version_de_unidad(
                valido_hasta="2100-03-01 00:00:00",
                es_vigente=0,
                version="2100-03-01 00:00:00",
            )
        )

        despues = _fila_del_condado()

        assert despues["unidades_vigentes"] == antes["unidades_vigentes"], (
            "la capacidad del período cambió al dar de baja la unidad después: "
            "el informe está contando la flota de hoy y reescribe el histórico"
        )
        assert despues["ratio"] == antes["ratio"]

    def test_una_unidad_dada_de_baja_antes_del_periodo_no_cuenta(self, escenario):
        # La comprobación simétrica: si contara siempre, la capacidad solo
        # crecería y el ratio de los meses recientes saldría siempre mejor.
        _cargar_unidad(
            _version_de_unidad(
                valido_hasta="2099-06-01 00:00:00",
                es_vigente=0,
                version="2099-06-01 00:00:00",
            )
        )

        fila = _fila_del_condado()

        assert fila["unidades_vigentes"] == 0
        assert fila["ratio"] is None, (
            "sin unidades el ratio es ausente, no cero: un 0 diría que hubo "
            "capacidad de sobra, que es lo contrario de lo que pasó"
        )
