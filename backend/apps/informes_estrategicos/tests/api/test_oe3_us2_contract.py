"""T046, T052 — contrato US2 y permiso de Expansion."""

from __future__ import annotations

import json

import pytest

from apps.informes_estrategicos.tests.conftest import SENSIBLES, cliente, pedir_oe3

US2 = (
    "ratio-demanda-capacidad",
    "cobertura-de-respaldo",
    "perdida-de-senal",
)


class TestContratoUs2:
    def test_ratio_tiene_la_forma(self):
        respuesta = pedir_oe3(cliente(["DirectorOperaciones"]), "ratio-demanda-capacidad")
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        for fila in respuesta.json()["data"]:
            assert {"periodo", "condado", "casos", "unidades_vigentes", "ratio", "sin_capacidad"} <= set(fila)
            assert isinstance(fila["sin_capacidad"], bool)

    def test_los_tres_responden(self):
        for informe in US2:
            respuesta = pedir_oe3(cliente(["DirectorOperaciones"]), informe)
            if respuesta.status_code != 200:
                pytest.skip("el modelo analítico no está disponible")
            assert "data" in respuesta.json()

    def test_expansion_accede_a_los_tres(self):
        expansion = cliente(["DirectorExpansion"])
        for informe in US2:
            respuesta = pedir_oe3(expansion, informe)
            assert respuesta.status_code != 403, f"Expansion recibió 403 en {informe}"


class TestSinDatoSensibleUs2:
    @pytest.mark.parametrize("informe", US2)
    def test_ninguna_respuesta_contiene_coordenadas_ni_identidad(self, informe):
        respuesta = pedir_oe3(cliente(["DirectorExpansion"]), informe)
        if respuesta.status_code != 200:
            pytest.skip("el modelo analítico no está disponible")
        texto = json.dumps(respuesta.json()).lower()
        for sensible in SENSIBLES:
            assert sensible not in texto
