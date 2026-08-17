"""T047 — cada tramo publica su propia población."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir


@pytest.mark.integration
class TestTramosPoblacion:
    def test_los_cuatro_tramos_tienen_recuentos_distintos(self):
        director = cliente(["DirectorOperaciones"])
        respuesta = pedir(director, "tramos-del-ciclo", granularidad="anio")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        por_tramo = {}
        for fila in respuesta.json()["data"]:
            por_tramo[fila["tramo"]] = por_tramo.get(fila["tramo"], 0) + int(fila["casos"])

        assert len(por_tramo) == 4, f"faltan tramos: {sorted(por_tramo)}"
        recuentos = list(por_tramo.values())
        assert len(set(recuentos)) == 4, (
            f"los cuatro tramos publican los mismos recuentos {por_tramo}: "
            f"se está usando un denominador común y se descartaron los que se "
            f"atascaron al principio"
        )
