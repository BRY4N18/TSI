"""T034 y T035 — la disponibilidad y los estados que el catálogo no tiene.

Las dos trampas del departamento, comprobadas sobre el resultado.

⚠️ **La peor de las dos es la disponibilidad**, porque falla con el signo
invertido. Contar transiciones asigna **0 % a la unidad que nunca falló** —no
tiene ninguna transición a «Fuera de servicio», ni ninguna en absoluto— así que
el informe que sirve para premiar a los proveedores fiables los señalaría como
los peores. Y no falla: devuelve un número plausible.

Con datos sintéticos, y es obligatorio: sobre los datos reales todas las unidades
salen al 100 %, así que una consulta correcta y una que devuelva siempre 1 se ven
exactamente igual.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import (  # noqa: E402
    cargar_transiciones,
    ejecutar_red_operativa,
    limpiar_transiciones,
    requiere_modelo,
    transicion,
)

#: El período de prueba es **un día**: 86 400 segundos.
DIA = 86_400


@pytest.fixture
def sin_transiciones():
    limpiar_transiciones()
    yield
    limpiar_transiciones()


def _de(unidad: str) -> dict:
    filas = [
        f for f in ejecutar_red_operativa("ot12_disponibilidad_declarada")
        if f["unidad"] == unidad
    ]
    return filas[0] if filas else {}


@requiere_modelo
class TestLaDisponibilidadSeMideEnTiempo:
    def test_una_unidad_activa_todo_el_periodo_sale_al_cien_por_cien(self, sin_transiciones):
        """⚠️ **Una sola transición, al principio, y nada más.**

        Es el caso que rompe el cálculo por transiciones: esta unidad no cambió
        de estado nunca, así que no hay «cambios a disponible» que contar. Con
        ese método saldría 0 % — el peor resultado posible al mejor
        comportamiento.
        """
        cargar_transiciones([transicion(1, unidad="U-BUENA", estado="Activa")])

        fila = _de("U-BUENA")

        assert fila["pct_disponibilidad"] == 1.0, (
            f"salió {fila.get('pct_disponibilidad')}: la unidad estuvo activa todo el "
            f"período y no cambió de estado nunca"
        )
        assert fila["segundos_medidos"] == DIA

    def test_una_unidad_activa_el_sesenta_por_ciento_sale_al_sesenta(self, sin_transiciones):
        # Activa hasta las 14:24 (el 60 % del día) y fuera de servicio el resto.
        cargar_transiciones([
            transicion(1, unidad="U-MEDIA", estado="Activa", hora="00:00:00"),
            transicion(2, unidad="U-MEDIA", estado="Fuera de servicio", hora="14:24:00"),
        ])

        fila = _de("U-MEDIA")

        assert fila["pct_disponibilidad"] == pytest.approx(0.6, abs=1e-3)
        assert fila["segundos_medidos"] == DIA

    def test_el_ultimo_tramo_llega_hasta_el_fin_del_periodo(self, sin_transiciones):
        """Sin esto, la unidad estable aportaría cero segundos y desaparecería.

        Es la otra mitad del primer caso: no basta con no contar transiciones,
        hay que cerrar el último tramo contra el fin del período.
        """
        cargar_transiciones([
            transicion(1, unidad="U-TARDE", estado="Activa", hora="18:00:00"),
        ])

        assert _de("U-TARDE")["segundos_medidos"] == 6 * 3600

    def test_una_unidad_sin_transiciones_conocidas_sale_ausente_y_no_cero(
        self, sin_transiciones
    ):
        """⚠️ Ausente y `0` significan cosas opuestas.

        * **Ausente** — no hay transiciones que digan en qué estado estuvo.
        * **`0`** — hubo transiciones y ninguna la dejó disponible.

        La primera no es una alarma; la segunda es la más grave que da este
        informe. Rellenar la ausencia con cero convierte silencio en catástrofe.
        """
        cargar_transiciones([transicion(1, unidad="U-OTRA", estado="Activa")])

        assert _de("U-SIN-DATOS") == {}, (
            "una unidad sin ninguna transición no debe aparecer con 0 %: no se "
            "sabe en qué estado estuvo"
        )

    def test_una_unidad_nunca_disponible_si_sale_a_cero(self, sin_transiciones):
        # La comprobación simétrica: el cero legítimo tiene que llegar. Tratarlo
        # todo como ausente escondería la alarma en vez de darla.
        cargar_transiciones([
            transicion(1, unidad="U-CAIDA", estado="Fuera de servicio", hora="00:00:00"),
        ])

        assert _de("U-CAIDA")["pct_disponibilidad"] == 0.0


@requiere_modelo
class TestEnMisionCuentaComoDisponible:
    def test_una_unidad_en_mision_esta_disponible(self, sin_transiciones):
        """Una unidad en misión **está trabajando**, que es lo contrario de no
        estar disponible. Y es justamente el estado que el catálogo no tiene.
        """
        cargar_transiciones([transicion(1, unidad="U-MISION", estado="En Misión")])

        assert _de("U-MISION")["pct_disponibilidad"] == 1.0


@requiere_modelo
class TestElEstadoQueElCatalogoNoTiene:
    """T035 — «En Misión» aparece pese a no estar en `Dim_EstadoUnidadEmergencia`."""

    def test_en_mision_aparece_en_el_reparto_por_estado(self, sin_transiciones):
        """Si falta, la consulta está uniendo con el catálogo del origen.

        Ese catálogo tiene tres filas y el histórico usa cuatro: un `INNER JOIN`
        devolvería el 87 % de las transiciones sin fallar, y lo que desaparecería
        es la actividad de las unidades trabajando.
        """
        cargar_transiciones([
            transicion(1, estado="Activa"),
            transicion(2, estado="En Misión", hora="01:00:00"),
            transicion(3, estado="Ocupada", hora="02:00:00"),
        ])

        por_estado = {
            f["estado"]: f["transiciones"] for f in ejecutar_red_operativa("ot12_unidades_por_estado")
        }

        assert "En Misión" in por_estado, (
            "'En Misión' desapareció del reparto: la consulta está uniendo con "
            "el catálogo de estados, que no lo tiene"
        )
        assert por_estado["En Misión"] == 1

    def test_un_estado_nulo_sale_como_desconocido_y_no_se_filtra(self, sin_transiciones):
        # Una transición sin estado es un defecto de datos que hay que ver, no
        # esconder: filtrarla haría que el reparto sumara menos que el total sin
        # que nada lo indicara.
        cargar_transiciones([
            transicion(1, estado="Activa"),
            transicion(2, estado=None, hora="01:00:00"),
        ])

        por_estado = {
            f["estado"]: f["transiciones"] for f in ejecutar_red_operativa("ot12_unidades_por_estado")
        }

        assert por_estado.get("Desconocido") == 1


@requiere_modelo
class TestLaSumaCuadra:
    """T036 — el reparto por estado suma el total de transiciones (SC-005)."""

    def test_la_suma_de_los_estados_es_el_total(self, sin_transiciones):
        cargar_transiciones([
            transicion(1, estado="Activa"),
            transicion(2, estado="En Misión", hora="01:00:00"),
            transicion(3, estado="Fuera de servicio", hora="02:00:00"),
            transicion(4, estado=None, hora="03:00:00"),
        ])

        filas = ejecutar_red_operativa("ot12_unidades_por_estado")

        assert sum(f["transiciones"] for f in filas) == 4, (
            "el reparto no suma el total: hay transiciones que se perdieron al "
            "clasificar, y los porcentajes seguirían sumando 100 % entre ellos"
        )
        assert sum(f["pct_transiciones"] for f in filas) == pytest.approx(1.0, abs=1e-3)
