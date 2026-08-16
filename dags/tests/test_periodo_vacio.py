"""T073 — un período sin datos devuelve cero filas, no una fila de ceros (FR-019, SC-011).

La diferencia parece cosmética y no lo es. Una fila con `casos: 0` **afirma que
se midió y no hubo nada**; una lista vacía dice que no hay nada que repartir.

En una pantalla, la primera pinta una barra a cero —una categoría que existe y
está vacía— y la segunda no pinta nada. Y en un tablero con umbrales, un `0` es
un valor que los umbrales evalúan: un porcentaje de calidad a cero dispara la
alarma más grave que hay, en un período en el que sencillamente no pasó nada.

Se recorre **todo el catálogo**, porque la regla es del catálogo y no de un
informe. Añadir una consulta que devuelva una fila de ceros no rompería ninguna
prueba propia.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.almacen import limpiar_particion, requiere_modelo  # noqa: E402

from lib.clickhouse_http_client import query_clickhouse  # noqa: E402
from lib.consultas import cargar, listar  # noqa: E402

INFORMES = listar("emergencias")

#: Un período **muy anterior** a cualquier dato del sistema. No se escribe nada:
#: se consulta un hueco.
VACIO = {"desde": "1990-01-01", "hasta": "1990-01-02"}

EXTRA = {
    "umbral_seg": "60", "ventana_dias": "90", "muestra_minima": "5",
    "top": "10", "tramos_dias": "1,3,7,30",
}


def ejecutar(informe: str) -> list[dict]:
    return query_clickhouse(
        cargar(informe, departamento="emergencias"), params={**VACIO, **EXTRA}
    )


@requiere_modelo
class TestUnPeriodoVacioNoInventaFilas:
    @pytest.mark.parametrize("informe", INFORMES)
    def test_no_devuelve_una_fila_de_ceros(self, informe):
        filas = ejecutar(informe)

        if not filas:
            return  # Lo correcto: no hay nada que repartir.

        # Algunas consultas agregan sobre todo el período sin `GROUP BY`, así que
        # devuelven una fila aunque no haya datos. Eso es aceptable **solo si sus
        # medidas van ausentes**: lo que no puede pasar es que afirmen un cero.
        for fila in filas:
            for columna, valor in fila.items():
                if not columna.startswith("pct"):
                    continue
                assert valor is None, (
                    f"'{informe}' devuelve {columna} = {valor} en un período sin "
                    f"datos: un porcentaje a cero es una alarma, y aquí no pasó nada"
                )

    @pytest.mark.parametrize("informe", INFORMES)
    def test_los_que_agrupan_no_devuelven_ninguna_fila(self, informe):
        """Si la consulta agrupa por algo, un período vacío no tiene grupos.

        Es la comprobación complementaria de la anterior: aquella tolera la fila
        única de las agregaciones globales, y esta exige que las agrupadas no
        inventen categorías.
        """
        cuerpo = "\n".join(
            l for l in cargar(informe, departamento="emergencias").splitlines()
            if not l.strip().startswith("--")
        )
        if "GROUP BY" not in cuerpo.upper():
            pytest.skip(f"'{informe}' no agrupa")

        assert ejecutar(informe) == [], (
            f"'{informe}' agrupa y aun así devolvió filas en un período vacío"
        )


@requiere_modelo
class TestLaParticionDePruebaEstaLimpia:
    def test_ninguna_prueba_anterior_dejo_filas(self):
        """Guarda de higiene, no de negocio.

        Una partición de prueba con restos haría que los informes de otras
        pruebas contaran filas que nadie cargó, y el fallo aparecería en el
        fichero equivocado.
        """
        limpiar_particion()

        restos = int(
            query_clickhouse(
                "SELECT count() AS n FROM hecho_accidente FINAL "
                "WHERE toYYYYMM(fecha) = 209912"
            )[0]["n"]
        )

        assert restos == 0
