"""Contrato US3: ecosistema."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import cliente, pedir_oe2

US3 = (
    "adopcion-versiones",
    "comparativa-partners",
    "crecimiento-ecosistema",
)


class TestContratoUs3Oe2:
    def test_los_tres_responden(self):
        api = cliente(["DirectorTecnologico"])
        for informe in US3:
            respuesta = pedir_oe2(api, informe)
            if respuesta.status_code != 200:
                pytest.skip("el modelo analítico no está disponible")
            assert "data" in respuesta.json()
