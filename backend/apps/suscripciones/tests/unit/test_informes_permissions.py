"""T010 — permisos de los informes de Suscripciones y Facturación.

**Dos clases, porque aquí la autoridad está repartida por materia.** El §5.1 del
SRS lo subraya y `acceso-tactico.md` lo recoge: Estrategia decide catálogo y
precios —suscripciones y cambios de plan—, y Financiero responde por el
resultado económico —facturas y medios de cobro—. Darles las cuatro a ambos
sería más simétrico y contradiría el SRS.

Y **no se reutiliza `IsProveedorCuenta`**: aquella clase admite solo Cliente y
Proveedor, así que un Administrador —la mitad del caso de uso táctico— recibiría
un rechazo.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from apps.suscripciones.permissions import (
    InformesCatalogoPermission,
    InformesFinanzasPermission,
)

CLASES = [InformesCatalogoPermission, InformesFinanzasPermission]


def _peticion(user):
    return SimpleNamespace(user=user)


def _usuario(*roles, autenticado=True):
    return SimpleNamespace(is_authenticated=autenticado, roles=list(roles))


class TestFallaCerrado:
    @pytest.mark.parametrize("clase", CLASES)
    def test_sin_usuario(self, clase):
        assert clase().has_permission(_peticion(None), None) is False

    @pytest.mark.parametrize("clase", CLASES)
    def test_sin_autenticar_aunque_traiga_el_rol(self, clase):
        user = _usuario("Administrador", autenticado=False)

        assert clase().has_permission(_peticion(user), None) is False

    @pytest.mark.parametrize("clase", CLASES)
    def test_autenticado_sin_roles(self, clase):
        assert clase().has_permission(_peticion(_usuario()), None) is False

    @pytest.mark.parametrize("clase", CLASES)
    def test_atributo_roles_en_none(self, clase):
        user = SimpleNamespace(is_authenticated=True, roles=None)

        assert clase().has_permission(_peticion(user), None) is False

    @pytest.mark.parametrize("clase", CLASES)
    def test_sin_atributo_roles(self, clase):
        user = SimpleNamespace(is_authenticated=True)

        assert clase().has_permission(_peticion(user), None) is False

    @pytest.mark.parametrize("clase", CLASES)
    @pytest.mark.parametrize("rol", ["Operador", "Tecnico", "GerenteVentas", "Despacho"])
    def test_rol_no_autorizado(self, clase, rol):
        assert clase().has_permission(_peticion(_usuario(rol)), None) is False


class TestConcede:
    @pytest.mark.parametrize("clase", CLASES)
    def test_el_administrador_accede_a_los_cuatro(self, clase):
        assert clase().has_permission(_peticion(_usuario("Administrador")), None) is True

    @pytest.mark.parametrize("clase", CLASES)
    @pytest.mark.parametrize("rol", ["Cliente", "Proveedor"])
    def test_los_roles_de_cuenta_acceden_a_los_cuatro(self, clase, rol):
        # Conceder aquí no implica ver todas las cuentas: el acotamiento por
        # organización los fuerza a la suya.
        assert clase().has_permission(_peticion(_usuario(rol)), None) is True


class TestLaAutoridadEstaRepartidaPorMateria:
    """§5.1 del SRS: no es una jefatura única."""

    def test_estrategia_accede_a_catalogo(self):
        user = _usuario("DirectorEstrategia")

        assert InformesCatalogoPermission().has_permission(_peticion(user), None) is True

    def test_estrategia_no_accede_a_finanzas(self):
        user = _usuario("DirectorEstrategia")

        assert InformesFinanzasPermission().has_permission(_peticion(user), None) is False

    def test_financiero_accede_a_finanzas(self):
        user = _usuario("DirectorFinanciero")

        assert InformesFinanzasPermission().has_permission(_peticion(user), None) is True

    def test_financiero_no_accede_a_catalogo(self):
        user = _usuario("DirectorFinanciero")

        assert InformesCatalogoPermission().has_permission(_peticion(user), None) is False

    def test_ninguna_autoridad_ajena_se_cuela(self):
        from core.auth.roles_tacticos import TODAS_LAS_AUTORIDADES

        ajenas = TODAS_LAS_AUTORIDADES - {"DirectorEstrategia", "DirectorFinanciero"}

        for clase in CLASES:
            for rol in ajenas:
                assert clase().has_permission(_peticion(_usuario(rol)), None) is False, (
                    f"'{rol}' es autoridad de otro departamento y no debe acceder aqui"
                )


class TestNoSeReutilizaElPermisoOperativo:
    def test_el_administrador_no_pasa_por_is_proveedor_cuenta(self):
        """La razón de que existan clases nuevas (research D1)."""
        from apps.suscripciones.permissions import IsProveedorCuenta

        import inspect

        fuente = inspect.getsource(IsProveedorCuenta)

        # Deja fuera al Administrador, que es la mitad del caso de uso táctico.
        assert "ROLE_ADMIN" not in fuente

    def test_las_clases_de_informes_no_heredan_de_la_operativa(self):
        from apps.suscripciones.permissions import IsProveedorCuenta

        for clase in CLASES:
            assert not issubclass(clase, IsProveedorCuenta)
