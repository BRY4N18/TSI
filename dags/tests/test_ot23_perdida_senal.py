"""T042 — la pérdida de señal no trunca.

El flujo anterior analizaba **10 000 de 59 045 posiciones** —el 16,9 %— y
publicaba el resultado como si fuera del total. No fallaba nada: la consulta no
llevaba `LIMIT` explícito y recibía el tope por defecto del cliente. Detectaba
714 huecos donde hay 3 942.

El truncamiento es invisible por construcción: la respuesta llega completa, con
su forma correcta y cifras verosímiles, y lo único que falta es el 83 % de los
datos — que no aparece en ninguna parte de la respuesta.

Por eso lo que se comprueba aquí es que **el denominador coincide con el origen**.
Comparar los huecos detectados no serviría: un número menor es indistinguible de
un período tranquilo.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    FECHA_DE_PRUEBA,
    cargar_pings,
    ejecutar_informe,
    limpiar_pings,
    ping,
    requiere_modelo,
)

from lib.clickhouse_http_client import query_clickhouse  # noqa: E402


@pytest.fixture
def sin_pings():
    limpiar_pings()
    yield
    limpiar_pings()


def _informe(umbral: int = 60) -> dict:
    filas = ejecutar_informe("ot23_perdida_senal", umbral_seg=umbral)
    return filas[0] if filas else {}


@requiere_modelo
class TestNoTrunca:
    def test_considera_todas_las_posiciones_del_periodo(self, sin_pings):
        # Más filas que el tope por defecto del cliente que causó el defecto
        # original. Si volviera a colarse un truncamiento, el denominador sería
        # menor que el origen y esta comprobación lo vería.
        cuantas = 12_000
        cargar_pings([ping(i, segundos_desde_anterior=10) for i in range(cuantas)])

        assert _informe()["intervalos_medidos"] == cuantas

    def test_el_denominador_coincide_con_el_origen_sobre_los_datos_reales(self):
        """Sobre el almacén entero, no sobre una partición fabricada.

        Es la comprobación que habría cazado el defecto original: el flujo viejo
        habría dado 10 000 aquí.
        """
        origen = int(
            query_clickhouse(
                "SELECT count() AS n FROM hecho_ping_unidad "
                "WHERE segundos_desde_anterior IS NOT NULL "
                "AND fecha BETWEEN '2026-01-01' AND '2026-12-31'"
            )[0]["n"]
        )
        filas = query_clickhouse(
            __import__("lib.consultas", fromlist=["cargar"]).cargar(
                "ot23_perdida_senal", departamento="emergencias"
            ),
            params={"desde": "2026-01-01", "hasta": "2026-12-31", "umbral_seg": "60"},
        )

        assert sum(f["intervalos_medidos"] for f in filas) == origen
        assert origen > 10_000, (
            "el origen tiene menos de 10 000 filas, así que esta prueba no "
            "distinguiría un truncamiento del tope por defecto"
        )


@requiere_modelo
class TestQueCuentaComoHueco:
    def test_solo_los_intervalos_mayores_que_el_umbral(self, sin_pings):
        cargar_pings([
            ping(1, segundos_desde_anterior=10),
            ping(2, segundos_desde_anterior=60),   # justo el umbral: no es hueco
            ping(3, segundos_desde_anterior=61),
        ])

        informe = _informe(umbral=60)

        assert informe["intervalos_medidos"] == 3
        assert informe["huecos"] == 1

    def test_la_primera_posicion_de_una_unidad_no_es_un_hueco_de_cero(self, sin_pings):
        """Su medida es nula porque no hay reporte anterior con el que medir.

        Un nulo no es un intervalo de cero segundos: es un intervalo que no
        existe. Contarlo como bueno inflaría la proporción de reportes correctos
        con datos que no miden nada.
        """
        cargar_pings([
            ping(1, segundos_desde_anterior=None),
            ping(2, segundos_desde_anterior=10),
        ])

        informe = _informe()

        assert informe["intervalos_medidos"] == 1, (
            "la primera posición entró en el denominador: no tiene intervalo que medir"
        )

    def test_el_umbral_cambia_el_resultado(self, sin_pings):
        cargar_pings([ping(i, segundos_desde_anterior=90) for i in range(3)])

        assert _informe(umbral=60)["huecos"] == 3
        assert _informe(umbral=120)["huecos"] == 0

    def test_publica_el_denominador_junto_a_los_huecos(self, sin_pings):
        # Es lo que permite ver que se miró todo. Un informe que solo publica el
        # número de huecos es indistinguible de uno truncado.
        cargar_pings([ping(1, segundos_desde_anterior=90)])

        assert "intervalos_medidos" in _informe()


@requiere_modelo
class TestPeriodoSinPosiciones:
    def test_sin_intervalos_medidos_el_porcentaje_es_nulo_y_no_cero(self, sin_pings):
        cargar_pings([ping(1, segundos_desde_anterior=None)])

        informe = _informe()

        assert informe["intervalos_medidos"] == 0
        assert informe["pct_huecos"] is None, (
            "un período sin intervalos medibles no tiene un 0 % de huecos: "
            "no tiene porcentaje"
        )
