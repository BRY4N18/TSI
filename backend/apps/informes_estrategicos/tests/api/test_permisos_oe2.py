"""Partner fuera. Tecnología no ve dinero. Finanzas sí. Gerente en ambas."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import (
    DINERO_OE2,
    INFORMES_OE2,
    cliente,
    pedir_oe2,
)

CONSUMO = "consumo-por-partner"
DINERO = "excedente-facturable"


class TestPermisosOe2:
    def test_tecnologico_entra_en_consumo(self):
        assert pedir_oe2(cliente(["DirectorTecnologico"]), CONSUMO).status_code != 403

    def test_tecnologico_recibe_403_en_dinero(self):
        respuesta = pedir_oe2(cliente(["DirectorTecnologico"]), DINERO)
        assert respuesta.status_code == 403
        assert respuesta.json().get("data") != []

    def test_financiero_entra_en_dinero(self):
        assert pedir_oe2(cliente(["DirectorFinanciero"]), DINERO).status_code != 403

    def test_gerente_entra_en_ambas(self):
        for informe in (CONSUMO, DINERO):
            assert pedir_oe2(cliente(["Gerente"]), informe).status_code != 403

    @pytest.mark.parametrize("informe", INFORMES_OE2)
    def test_partner_recibe_403_en_los_diez(self, informe):
        respuesta = pedir_oe2(cliente(["PartnerIntegracion"]), informe)
        assert respuesta.status_code == 403
        assert respuesta.json().get("data") != []

    @pytest.mark.parametrize("roles", [["Operador"], ["Administrador"], ["DirectorOperaciones"]])
    def test_ajenos_reciben_403(self, roles):
        assert pedir_oe2(cliente(roles), CONSUMO).status_code == 403

    @pytest.mark.parametrize("informe", DINERO_OE2)
    def test_tecnologico_fuera_de_los_tres_de_dinero(self, informe):
        assert pedir_oe2(cliente(["DirectorTecnologico"]), informe).status_code == 403
