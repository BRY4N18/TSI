"""Permiso de OE6 y OE3, sin HTTP: cubre la clase además del 403."""

from types import SimpleNamespace

from apps.informes_estrategicos.permissions import (
    Oe1Permission,
    Oe3Permission,
    Oe5Permission,
    Oe6Permission,
)


def _pide(roles):
    usuario = SimpleNamespace(is_authenticated=True, roles=roles)
    return Oe6Permission().has_permission(SimpleNamespace(user=usuario), None)


def _pide_oe3(roles, informe):
    usuario = SimpleNamespace(is_authenticated=True, roles=roles)
    vista = SimpleNamespace(kwargs={"informe": informe})
    return Oe3Permission().has_permission(SimpleNamespace(user=usuario), vista)


class TestOe6Permission:
    def test_director_y_gerente_entran(self):
        assert _pide(["DirectorOperaciones"]) is True
        assert _pide(["Gerente"]) is True

    def test_operativo_no_entra(self):
        assert _pide(["Operador"]) is False
        assert _pide(["Administrador"]) is False
        assert _pide([]) is False


def _pide_oe1(roles, informe):
    usuario = SimpleNamespace(is_authenticated=True, roles=roles)
    vista = SimpleNamespace(kwargs={"informe": informe})
    return Oe1Permission().has_permission(SimpleNamespace(user=usuario), vista)


class TestOe1Permission:
    def test_marketing_no_entra_en_mrr(self):
        assert _pide_oe1(["DirectorMarketing"], "mrr-mensual") is False

    def test_financiero_entra_en_mrr(self):
        assert _pide_oe1(["DirectorFinanciero"], "mrr-mensual") is True

    def test_ciclo_solo_gerente(self):
        assert _pide_oe1(["DirectorEstrategia"], "tiempo-onboarding") is False
        assert _pide_oe1(["Gerente"], "tiempo-onboarding") is True

    def test_bloqueado_no_da_403_a_autoridad(self):
        assert _pide_oe1(["Gerente"], "cac-por-canal") is True
        assert _pide_oe1(["PartnerIntegracion"], "cac-por-canal") is False


def _pide_oe5(roles, informe):
    usuario = SimpleNamespace(is_authenticated=True, roles=roles)
    vista = SimpleNamespace(kwargs={"informe": informe})
    return Oe5Permission().has_permission(SimpleNamespace(user=usuario), vista)


class TestOe5Permission:
    def test_financiero_no_entra_en_sla(self):
        assert _pide_oe5(["DirectorFinanciero"], "cumplimiento-sla") is False

    def test_exito_cliente_entra_en_sla(self):
        assert _pide_oe5(["GerenteExitoCliente"], "cumplimiento-sla") is True

    def test_riesgo_solo_gerente(self):
        assert _pide_oe5(["DirectorEstrategia"], "cuentas-en-riesgo") is False
        assert _pide_oe5(["Gerente"], "cuentas-en-riesgo") is True

    def test_bloqueado_no_da_403_a_autoridad(self):
        assert _pide_oe5(["Gerente"], "nps-satisfaccion") is True
        assert _pide_oe5(["PartnerIntegracion"], "nps-satisfaccion") is False


class TestOe3Permission:
    def test_expansion_no_entra_en_despacho(self):
        assert _pide_oe3(["DirectorExpansion"], "latencia-asignacion") is False

    def test_expansion_entra_en_capacidad(self):
        assert _pide_oe3(["DirectorExpansion"], "ratio-demanda-capacidad") is True

    def test_operaciones_entra_en_ambos(self):
        assert _pide_oe3(["DirectorOperaciones"], "latencia-asignacion") is True
        assert _pide_oe3(["DirectorOperaciones"], "ratio-demanda-capacidad") is True
