"""Exclusión OE5: Finanzas no ve SLA; Éxito Cliente no ve NRR; riesgo solo Gerente."""

from __future__ import annotations

import pytest

from apps.informes_estrategicos.tests.conftest import INFORMES_OE5, cliente, pedir_oe5


class TestPermisosOe5:
    def test_financiero_recibe_403_en_sla(self):
        respuesta = pedir_oe5(cliente(["DirectorFinanciero"]), "cumplimiento-sla")
        assert respuesta.status_code == 403
        assert respuesta.json().get("data") != []

    def test_exito_cliente_recibe_403_en_nrr(self):
        respuesta = pedir_oe5(cliente(["GerenteExitoCliente"]), "retencion-neta-ingresos")
        assert respuesta.status_code == 403

    def test_estrategia_recibe_403_en_riesgo(self):
        respuesta = pedir_oe5(cliente(["DirectorEstrategia"]), "cuentas-en-riesgo")
        assert respuesta.status_code == 403

    def test_exito_cliente_entra_en_sla(self):
        assert pedir_oe5(cliente(["GerenteExitoCliente"]), "cumplimiento-sla").status_code != 403

    def test_financiero_entra_en_nrr(self):
        assert pedir_oe5(cliente(["DirectorFinanciero"]), "retencion-neta-ingresos").status_code != 403

    def test_estrategia_entra_en_movimientos_y_antiguedad(self):
        assert pedir_oe5(cliente(["DirectorEstrategia"]), "movimientos-de-plan").status_code != 403
        assert pedir_oe5(cliente(["DirectorEstrategia"]), "antiguedad-de-cuenta").status_code != 403

    @pytest.mark.parametrize("informe", INFORMES_OE5)
    def test_gerente_no_recibe_403_en_los_nueve(self, informe):
        assert pedir_oe5(cliente(["Gerente"]), informe).status_code != 403

    @pytest.mark.parametrize("informe", INFORMES_OE5)
    def test_partner_recibe_403_en_los_nueve(self, informe):
        respuesta = pedir_oe5(cliente(["PartnerIntegracion"]), informe)
        assert respuesta.status_code == 403
        assert respuesta.json().get("data") != []
