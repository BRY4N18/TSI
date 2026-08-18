"""Exclusión OE1: Marketing no ve MRR; Finanzas no ve embudo; ciclo solo Gerente."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import (
    CICLO_OE1,
    INFORMES_OE1,
    cliente,
    pedir_oe1,
)


class TestPermisosOe1:
    def test_marketing_recibe_403_en_mrr(self):
        respuesta = pedir_oe1(cliente(["DirectorMarketing"]), "mrr-mensual")
        assert respuesta.status_code == 403
        assert respuesta.json().get("data") != []

    def test_financiero_recibe_403_en_embudo(self):
        respuesta = pedir_oe1(cliente(["DirectorFinanciero"]), "embudo-conversion")
        assert respuesta.status_code == 403

    def test_estrategia_recibe_403_en_onboarding(self):
        respuesta = pedir_oe1(cliente(["DirectorEstrategia"]), "tiempo-onboarding")
        assert respuesta.status_code == 403

    def test_financiero_entra_en_mrr(self):
        assert pedir_oe1(cliente(["DirectorFinanciero"]), "mrr-mensual").status_code != 403

    def test_estrategia_entra_en_segmento_y_cartera(self):
        assert pedir_oe1(cliente(["DirectorEstrategia"]), "mrr-por-segmento").status_code != 403
        assert pedir_oe1(cliente(["DirectorEstrategia"]), "cartera-por-plan").status_code != 403

    def test_marketing_entra_en_embudo(self):
        assert pedir_oe1(cliente(["DirectorMarketing"]), "embudo-conversion").status_code != 403

    @pytest.mark.parametrize("informe", INFORMES_OE1)
    def test_gerente_no_recibe_403_en_los_diez(self, informe):
        assert pedir_oe1(cliente(["Gerente"]), informe).status_code != 403

    @pytest.mark.parametrize("informe", INFORMES_OE1)
    def test_partner_recibe_403_en_los_diez(self, informe):
        respuesta = pedir_oe1(cliente(["PartnerIntegracion"]), informe)
        assert respuesta.status_code == 403
        assert respuesta.json().get("data") != []

    @pytest.mark.parametrize("informe", CICLO_OE1)
    def test_ciclo_solo_gerente(self, informe):
        assert pedir_oe1(cliente(["DirectorFinanciero"]), informe).status_code == 403
        assert pedir_oe1(cliente(["DirectorMarketing"]), informe).status_code == 403
        assert pedir_oe1(cliente(["Gerente"]), informe).status_code != 403
