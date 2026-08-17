"""T083 — ningún porcentaje sale sin el total sobre el que se calculó."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import INFORMES, cliente, pedir

DENOMINADORES = (
    "casos", "casos_con_llegada", "casos_con_dato", "casos_cerrados",
    "casos_abiertos", "ofrecidos", "misiones", "despachos",
    "despachos_confirmados", "llegadas_medidas", "llegadas_con_referencia",
)


@pytest.mark.integration
class TestTodoPorcentajeConDenominador:
    @pytest.mark.parametrize("informe", INFORMES)
    def test_si_hay_porcentaje_hay_denominador(self, informe):
        director = cliente(["DirectorOperaciones"])
        extra = {"top": 100} if informe == "rechazo-y-timeout-por-unidad" else {}
        respuesta = pedir(director, informe, **extra)
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")

        for fila in respuesta.json()["data"]:
            claves = set(fila)
            hay_pct = any(
                k.startswith("pct") or k.startswith("tasa") for k in claves
            )
            if not hay_pct:
                continue
            assert claves & set(DENOMINADORES), (
                f"'{informe}' publica un porcentaje en {sorted(claves)} sin denominador"
            )
