"""T064 — el denominador de la tasa de rechazo son intentos, no transiciones.

Añadir despachos confirmados a una unidad no debe bajar su tasa por el factor
2,6 del defecto #34 (cada despacho bien atendido añadía ~4 transiciones al
denominador). Aquí tasa_rechazo = rechazados / ofrecidos, y ofrecidos es el
número de filas de despacho.
"""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir


@pytest.mark.integration
class TestDenominadorIntentos:
    def test_la_tasa_es_rechazados_entre_ofrecidos(self):
        director = cliente(["DirectorOperaciones"])
        respuesta = pedir(director, "rechazo-y-timeout-por-unidad", top=100, granularidad="anio")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        filas = respuesta.json()["data"]
        assert filas
        for fila in filas:
            ofrecidos = int(fila["ofrecidos"])
            rechazados = int(fila["rechazados"])
            assert rechazados <= ofrecidos
            if ofrecidos == 0:
                continue
            esperada = round(rechazados / ofrecidos, 4)
            assert fila["tasa_rechazo"] == pytest.approx(esperada, abs=0.0001), (
                f"{fila['unidad']}: tasa {fila['tasa_rechazo']} no es "
                f"{rechazados}/{ofrecidos}. Si el denominador fueran transiciones, "
                f"añadir despachos confirmados bajaría la tasa de más"
            )
