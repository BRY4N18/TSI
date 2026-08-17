"""Permiso de OE6 y OE3, sin HTTP: cubre la clase además del 403."""

from types import SimpleNamespace

from apps.informes_estrategicos.permissions import Oe3Permission, Oe6Permission


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


class TestOe3Permission:
    def test_expansion_no_entra_en_despacho(self):
        assert _pide_oe3(["DirectorExpansion"], "latencia-asignacion") is False

    def test_expansion_entra_en_capacidad(self):
        assert _pide_oe3(["DirectorExpansion"], "ratio-demanda-capacidad") is True

    def test_operaciones_entra_en_ambos(self):
        assert _pide_oe3(["DirectorOperaciones"], "latencia-asignacion") is True
        assert _pide_oe3(["DirectorOperaciones"], "ratio-demanda-capacidad") is True
