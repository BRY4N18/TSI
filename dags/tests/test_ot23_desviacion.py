"""T043 — la referencia de llegada (SC-011). Cuatro comprobaciones.

`segundos_referencia` no es un compromiso operativo: el sistema no guarda
ninguna estimación de llegada, así que la referencia se **deriva** del histórico.
Eso hace que su construcción sea toda la sustancia del informe, y cada una de las
cuatro decisiones que la definen falla en silencio si se toma al revés:

1. **Mediana y no promedio** — un atasco de dos horas desplaza el promedio y deja
   la referencia en un valor al que ninguna llegada real se parece.
2. **Ventana anterior** — si incluyera el período medido, cada unidad se
   compararía en parte consigo misma y una unidad lenta saldría normal.
3. **Sin muestra suficiente, ausente y no cero** — un `0` diría «llegó justo a
   tiempo» y convertiría una unidad sin histórico en una unidad ejemplar.
4. **Sin llegada, fuera del cálculo** — contar como cero a quien nunca llegó la
   haría parecer instantánea.
"""

from __future__ import annotations

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

CONDADO = "Condado de prueba T043"
#: Un día del mes **anterior** al medido, dentro de la ventana de referencia.
FECHA_ANTERIOR = "2099-11-15"
PARTICION_ANTERIOR = 209911


@pytest.fixture
def sin_despachos():
    _limpiar()
    yield
    _limpiar()


def _limpiar():
    limpiar_despachos()
    execute_clickhouse(
        f"ALTER TABLE hecho_despacho DROP PARTITION {PARTICION_ANTERIOR}"
    )


def _informe(*, ventana_dias: int = 90, muestra_minima: int = 5) -> dict:
    filas = ejecutar_informe(
        "ot23_desviacion_llegada",
        ventana_dias=ventana_dias,
        muestra_minima=muestra_minima,
    )
    propias = [f for f in filas if f["unidad"] == "T043-UNI"]
    return propias[0] if propias else {}


def _historico(segundos: list[int], fecha: str = FECHA_ANTERIOR) -> list[dict]:
    """Despachos comparables en la ventana anterior."""
    return [
        despacho(
            5000 + i, idaccidente=f"T043-h{i}", unidad="T043-OTRA", condado=CONDADO,
            segundos_transito=s, fecha=fecha,
        )
        for i, s in enumerate(segundos)
    ]


def _medidos(segundos: list[int]) -> list[dict]:
    """Despachos de la unidad medida, dentro del período consultado."""
    return [
        despacho(
            6000 + i, idaccidente=f"T043-m{i}", unidad="T043-UNI", condado=CONDADO,
            segundos_transito=s,
        )
        for i, s in enumerate(segundos)
    ]


@requiere_modelo
class TestUsaMedianaYNoPromedio:
    def test_un_valor_extremo_no_arrastra_la_referencia(self, sin_despachos):
        # Cinco llegadas de ~400 s y una de dos horas. La mediana es 400; el
        # promedio, más de 1600. La diferencia decide si la unidad medida sale
        # lenta o rapidísima.
        cargar_despachos(
            _historico([400, 400, 400, 400, 400, 7200]) + _medidos([400])
        )

        fila = _informe()

        assert fila["segundos_referencia"] == 400, (
            f"la referencia salió {fila['segundos_referencia']}: si está cerca "
            f"del promedio (~1533), se está usando promedio y no mediana"
        )
        assert fila["desviacion_mediana"] == 0


@requiere_modelo
class TestLaVentanaEsAnterior:
    def test_los_despachos_medidos_no_entran_en_su_propia_referencia(self, sin_despachos):
        """La unidad medida es muy lenta y el histórico muy rápido.

        Si la referencia incluyera el período medido, se contaminaría con las
        llegadas lentas y la desviación saldría mucho menor de lo real — la
        unidad lenta se estaría comparando consigo misma.
        """
        cargar_despachos(
            _historico([100, 100, 100, 100, 100])
            + _medidos([1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000])
        )

        fila = _informe()

        assert fila["segundos_referencia"] == 100, (
            f"la referencia salió {fila['segundos_referencia']} en vez de 100: "
            f"la ventana está incluyendo los despachos que se están midiendo"
        )
        assert fila["desviacion_mediana"] == 900

    def test_lo_anterior_a_la_ventana_no_cuenta(self, sin_despachos):
        # Con una ventana de 7 días, un histórico de hace medio mes queda fuera
        # y la unidad se queda sin referencia comparable.
        cargar_despachos(_historico([100] * 10) + _medidos([500]))

        assert _informe(ventana_dias=7)["segundos_referencia"] is None


@requiere_modelo
class TestMuestraInsuficiente:
    def test_sin_muestra_minima_la_referencia_es_ausente_y_no_cero(self, sin_despachos):
        # Dos llegadas comparables. La mediana existe aritméticamente y no
        # significa nada: es un dato anecdótico presentado como norma.
        cargar_despachos(_historico([400, 400]) + _medidos([500]))

        fila = _informe(muestra_minima=5)

        assert fila["segundos_referencia"] is None, (
            "con muestra insuficiente la referencia tiene que ser ausente"
        )
        assert fila["desviacion_mediana"] is None, (
            "un 0 diría «llegó justo a tiempo», que es lo contrario de "
            "«no sabemos qué esperar»"
        )
        # El dato propio de la unidad sí se publica: no saber con qué compararlo
        # no es razón para ocultar cuánto tardó.
        assert fila["segundos_reales_mediana"] == 500
        assert fila["llegadas_con_referencia"] == 0

    def test_con_muestra_suficiente_la_referencia_aparece(self, sin_despachos):
        cargar_despachos(_historico([400] * 5) + _medidos([500]))

        fila = _informe(muestra_minima=5)

        assert fila["segundos_referencia"] == 400
        assert fila["desviacion_mediana"] == 100
        assert fila["llegadas_con_referencia"] == 1


@requiere_modelo
class TestDespachosSinLlegada:
    def test_quedan_fuera_del_calculo_y_no_cuentan_como_cero(self, sin_despachos):
        """Un rechazo no es una llegada instantánea.

        `segundos_transito` es nulo cuando la unidad no llegó. Si esos nulos
        entraran como ceros, la unidad que menos aparece saldría como la más
        rápida — y ese es el ranking que alguien usaría para premiarla.
        """
        cargar_despachos(
            _historico([400] * 5)
            + _medidos([500, 500])
            + [
                despacho(6900, idaccidente="T043-r", unidad="T043-UNI",
                         condado=CONDADO, resultado="rechazado", segundos_transito=None),
                despacho(6901, idaccidente="T043-v", unidad="T043-UNI",
                         condado=CONDADO, resultado="vencido", segundos_transito=None),
            ]
        )

        fila = _informe()

        assert fila["llegadas_medidas"] == 2, (
            "los despachos sin llegada entraron en el cálculo"
        )
        assert fila["segundos_reales_mediana"] == 500

    def test_no_inflan_el_recuento_de_la_muestra_comparable(self, sin_despachos):
        """El punto exacto donde los no-llegados harían daño.

        La mediana los ignora sola —`median()` descarta los nulos—, así que
        colarlos en la ventana **no** desplaza la referencia. Donde sí cuentan es
        en `llegadas_comparables`, el número que decide si hay muestra
        suficiente: veinte rechazos y dos llegadas darían una muestra de
        veintidós, se superaría el mínimo, y se publicaría como norma la mediana
        de **dos** llegadas.

        Ese es el fallo, y no es el que parecía: no es una referencia
        desplazada, es una referencia que no debería existir presentada como
        sólida.
        """
        cargar_despachos(
            _historico([400, 400])           # solo dos llegadas de verdad
            + [
                despacho(5900 + i, idaccidente=f"T043-hr{i}", unidad="T043-OTRA",
                         condado=CONDADO, resultado="rechazado",
                         segundos_transito=None, fecha=FECHA_ANTERIOR)
                for i in range(20)
            ]
            + _medidos([400])
        )

        assert _informe(muestra_minima=5)["segundos_referencia"] is None, (
            "la muestra se dio por suficiente contando despachos sin llegada: "
            "se publicaría como norma la mediana de dos llegadas"
        )
