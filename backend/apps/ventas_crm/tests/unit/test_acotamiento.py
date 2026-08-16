"""T007 — el resolutor de acotamiento por titularidad (research D2).

Cubre las **seis combinaciones** de la tabla de research D2, y muy en particular
la que da nombre a esta prueba: **pedir lo ajeno nunca devuelve datos propios**.

Por qué esa es la importante
----------------------------
La alternativa tentadora es «si pide la cartera de otro, devuélvele la suya».
Nadie ve un error, el endpoint responde `200`, y el resultado es un informe que
**parece responder a una pregunta que nadie hizo**. Peor: le oculta al
solicitante que pidió algo indebido, así que ni siquiera puede corregirlo.

Este módulo es el que heredan los seis departamentos restantes. Un fallo aquí no
se queda aquí.
"""

from __future__ import annotations

import pytest

from core.informes.acotamiento import (
    ACOTADO_PROPIOS,
    ACOTADO_TODOS,
    AccesoDenegado,
    resolver,
)

AMPLIOS = ["Administrador", "DirectorMarketing"]
ACOTADOS = ["GerenteVentas", "GerenteCuentasPublicas"]

YO = 42
OTRO = 99


def _resolver(roles, titular_pedido=None, user_id=YO):
    return resolver(
        roles=roles,
        user_id=user_id,
        roles_amplios=AMPLIOS,
        roles_acotados=ACOTADOS,
        titular_pedido=titular_pedido,
    )


class TestRolAmplio:
    """Ve todo, y puede elegir mirar a uno."""

    @pytest.mark.parametrize("rol", AMPLIOS)
    def test_sin_titular_no_acota(self, rol):
        acotamiento = _resolver([rol])

        assert acotamiento.titular is None
        assert acotamiento.acotado is False
        assert acotamiento.alcance == ACOTADO_TODOS

    @pytest.mark.parametrize("rol", AMPLIOS)
    def test_con_titular_filtra_por_ese(self, rol):
        acotamiento = _resolver([rol], titular_pedido=OTRO)

        assert acotamiento.titular == OTRO

    def test_filtrar_no_reduce_su_alcance_declarado(self):
        # Sigue teniendo acceso a todos: ha elegido mirar a uno. Declararlo como
        # `propios` le haría creer que está viendo su propia cartera.
        acotamiento = _resolver(["Administrador"], titular_pedido=OTRO)

        assert acotamiento.alcance == ACOTADO_TODOS

    def test_puede_filtrar_por_si_mismo(self):
        assert _resolver(["Administrador"], titular_pedido=YO).titular == YO


class TestRolAcotado:
    """Forzado a lo suyo; pedir lo ajeno es negativa."""

    @pytest.mark.parametrize("rol", ACOTADOS)
    def test_sin_titular_queda_forzado_a_lo_suyo(self, rol):
        acotamiento = _resolver([rol])

        assert acotamiento.titular == YO
        assert acotamiento.acotado is True
        assert acotamiento.alcance == ACOTADO_PROPIOS

    @pytest.mark.parametrize("rol", ACOTADOS)
    def test_pedirse_a_si_mismo_es_valido(self, rol):
        assert _resolver([rol], titular_pedido=YO).titular == YO

    @pytest.mark.parametrize("rol", ACOTADOS)
    def test_pedir_lo_ajeno_es_negativa(self, rol):
        with pytest.raises(AccesoDenegado):
            _resolver([rol], titular_pedido=OTRO)

    @pytest.mark.parametrize("rol", ACOTADOS)
    def test_pedir_lo_ajeno_no_devuelve_lo_propio(self, rol):
        """La garantía central de research D2.

        Una sustitución silenciosa produce un informe plausible que responde a
        una pregunta que nadie hizo.
        """
        try:
            acotamiento = _resolver([rol], titular_pedido=OTRO)
        except AccesoDenegado:
            return  # comportamiento correcto

        pytest.fail(
            f"devolvio un acotamiento (titular={acotamiento.titular}) en vez de negar; "
            "sustituir la cartera ajena por la propia oculta al solicitante que pidio algo indebido"
        )

    def test_el_titular_se_compara_como_entero(self):
        # `?ejecutivo=42` llega como texto desde la URL; compararlo sin convertir
        # haría que un gerente pudiera "pedirse a sí mismo" y recibir negativa.
        assert _resolver(["GerenteVentas"], titular_pedido="42").titular == YO


class TestRolNoReconocido:
    @pytest.mark.parametrize(
        "roles", [[], None, ["Operador"], ["Cliente"], ["PartnerIntegracion"], ["Tecnico"]]
    )
    def test_siempre_negativa(self, roles):
        with pytest.raises(AccesoDenegado):
            _resolver(roles)

    def test_negativa_tambien_si_pide_un_titular(self):
        with pytest.raises(AccesoDenegado):
            _resolver(["Operador"], titular_pedido=YO)

    def test_un_rol_desconocido_no_cae_en_la_rama_de_ver_todo(self):
        """El orden de las comprobaciones importa.

        Si el titular se resolviera antes que el rol, un rol desconocido sin
        `titular_pedido` caería en «no filtrar» — es decir, vería todo.
        """
        with pytest.raises(AccesoDenegado):
            _resolver(["RolInventado"], titular_pedido=None)


class TestRolesAcumulados:
    """Un usuario acumula roles vía `Dim_Usuario_Rol`."""

    def test_amplio_mas_acotado_gana_el_amplio(self):
        acotamiento = _resolver(["GerenteVentas", "Administrador"])

        assert acotamiento.titular is None
        assert acotamiento.alcance == ACOTADO_TODOS

    def test_acotado_mas_rol_irrelevante_sigue_acotado(self):
        acotamiento = _resolver(["GerenteVentas", "Operador"])

        assert acotamiento.titular == YO


class TestConfiguracionIncoherente:
    def test_un_rol_en_ambos_conjuntos_falla_al_configurar(self):
        # El resultado dependería del orden de evaluación, es decir del azar.
        # Mejor detectarlo aquí que en producción con datos de por medio.
        with pytest.raises(ValueError, match="GerenteVentas"):
            resolver(
                roles=["GerenteVentas"],
                user_id=YO,
                roles_amplios=["Administrador", "GerenteVentas"],
                roles_acotados=["GerenteVentas"],
            )
