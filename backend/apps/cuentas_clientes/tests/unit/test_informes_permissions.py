"""T011 — las dos clases de permiso de los listados, que deben fallar cerrado.

"Fallar cerrado" significa que la negativa es el valor por defecto: solo concede
quien tiene el rol, y cualquier forma de ausencia —sin token, sin autenticar,
sin roles, con el atributo a `None`— niega. Un permiso que conceda por descuido
en uno de esos huecos convierte el informe en la puerta trasera que el contrato
comun existe para impedir.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from apps.cuentas_clientes.permissions import (
    InformesAccesosTecnicosPermission,
    InformesCuentasLecturaPermission,
)

CLASES = [InformesCuentasLecturaPermission, InformesAccesosTecnicosPermission]


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
    @pytest.mark.parametrize("rol", ["Operador", "Cliente", "Tecnico", "PartnerIntegracion"])
    def test_rol_no_autorizado(self, clase, rol):
        assert clase().has_permission(_peticion(_usuario(rol)), None) is False


class TestConcede:
    @pytest.mark.parametrize("clase", CLASES)
    def test_administrador_accede_a_los_ocho(self, clase):
        assert clase().has_permission(_peticion(_usuario("Administrador")), None) is True

    @pytest.mark.parametrize("clase", CLASES)
    def test_un_rol_valido_entre_varios_basta(self, clase):
        # Un usuario acumula roles via `Dim_Usuario_Rol`; llevar otros no resta.
        user = _usuario("Operador", "Administrador")

        assert clase().has_permission(_peticion(user), None) is True


class TestElDirectorTecnologicoSoloEnAccesosTecnicos:
    """`acceso-tactico.md` §5 ⚠️ — ampliarlo contradiria el §5.1 del SRS."""

    def test_accede_a_accesos_tecnicos(self):
        user = _usuario("DirectorTecnologico")

        assert InformesAccesosTecnicosPermission().has_permission(_peticion(user), None) is True

    def test_no_accede_a_los_otros_siete(self):
        user = _usuario("DirectorTecnologico")

        assert InformesCuentasLecturaPermission().has_permission(_peticion(user), None) is False


def test_ninguna_autoridad_ajena_se_cuela():
    """Cuentas y Clientes no tiene autoridad de negocio: es lo que dice el §5.1."""
    from core.auth.roles_tacticos import TODAS_LAS_AUTORIDADES

    ajenas = TODAS_LAS_AUTORIDADES - {"DirectorTecnologico"}
    permiso = InformesCuentasLecturaPermission()

    for rol in ajenas:
        assert permiso.has_permission(_peticion(_usuario(rol)), None) is False, (
            f"'{rol}' es autoridad de otro departamento y no debe acceder aqui"
        )
