"""T010 — las clases de permiso de los informes de Ventas y CRM, que fallan cerrado.

Dos clases y no una, porque **reasignaciones no es como los otros tres**: es
supervisión pura. Un gerente no accede ni siquiera acotado a lo suyo, porque el
reparto de cartera es una decisión *sobre* él, no una herramienta *suya*, y
dársela acotada le mostraría de quién recibió o a quién perdió prospectos
—información de jefatura— disfrazada de listado propio.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from apps.ventas_crm.permissions import (
    InformesReasignacionesPermission,
    InformesVentasLecturaPermission,
)

CLASES = [InformesVentasLecturaPermission, InformesReasignacionesPermission]


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
        assert clase().has_permission(_peticion(SimpleNamespace(is_authenticated=True)), None) is False

    @pytest.mark.parametrize("clase", CLASES)
    @pytest.mark.parametrize("rol", ["Operador", "Cliente", "Tecnico", "PartnerIntegracion"])
    def test_rol_no_autorizado(self, clase, rol):
        assert clase().has_permission(_peticion(_usuario(rol)), None) is False


class TestRolAmplio:
    @pytest.mark.parametrize("clase", CLASES)
    @pytest.mark.parametrize("rol", ["Administrador", "DirectorMarketing"])
    def test_accede_a_los_cuatro(self, clase, rol):
        assert clase().has_permission(_peticion(_usuario(rol)), None) is True


class TestGerentes:
    @pytest.mark.parametrize("rol", ["GerenteVentas", "GerenteCuentasPublicas"])
    def test_acceden_a_cartera_demos_y_notificaciones(self, rol):
        permiso = InformesVentasLecturaPermission()

        assert permiso.has_permission(_peticion(_usuario(rol)), None) is True

    @pytest.mark.parametrize("rol", ["GerenteVentas", "GerenteCuentasPublicas"])
    def test_no_acceden_a_reasignaciones(self, rol):
        permiso = InformesReasignacionesPermission()

        assert permiso.has_permission(_peticion(_usuario(rol)), None) is False


class TestLaAutoridadDepartamental:
    def test_el_director_de_marketing_es_rol_amplio_no_acotado(self):
        """§5.1 del SRS: accede sin acotamiento por titularidad."""
        from apps.ventas_crm.permissions import (
            ROLES_INFORMES_ACOTADOS,
            ROLES_INFORMES_AMPLIOS,
        )

        assert "DirectorMarketing" in ROLES_INFORMES_AMPLIOS
        assert "DirectorMarketing" not in ROLES_INFORMES_ACOTADOS

    def test_ninguna_autoridad_de_otro_departamento_accede(self):
        from core.auth.roles_tacticos import TODAS_LAS_AUTORIDADES

        ajenas = TODAS_LAS_AUTORIDADES - {"DirectorMarketing"}
        permiso = InformesVentasLecturaPermission()

        for rol in ajenas:
            assert permiso.has_permission(_peticion(_usuario(rol)), None) is False, (
                f"'{rol}' es autoridad de otro departamento y no debe acceder aqui"
            )
