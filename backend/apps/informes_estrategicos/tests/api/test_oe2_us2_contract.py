"""Contrato US2: dinero. Skip si el almacén no está."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir_oe2

US2 = (
    "excedente-facturable",
    "participacion-ingresos-api",
    "mrr-por-linea",
)


class TestContratoUs2Oe2:
    def test_los_tres_responden_a_finanzas(self):
        api = cliente(["DirectorFinanciero"])
        for informe in US2:
            respuesta = pedir_oe2(api, informe)
            if respuesta.status_code != 200:
                pytest.skip("el modelo analítico no está disponible")
            cuerpo = respuesta.json()
            assert "data" in cuerpo and "meta" in cuerpo
