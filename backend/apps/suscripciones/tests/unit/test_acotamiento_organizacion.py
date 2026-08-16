"""T007 — el eje «organización» del acotamiento (research D1).

Es el segundo eje de la pieza transversal. El primero —«persona», de Ventas y
CRM— asume que el titular *es* el solicitante; aquí hay un **salto de
indirección**: el usuario pregunta y el resultado se acota a la cuenta cliente a
la que pertenece.

Cubre las seis combinaciones de la tabla de research D1, y la garantía que da
nombre a la prueba: **pedir otra cuenta nunca devuelve datos propios**. La
sustitución silenciosa es peor que la negativa, por las mismas dos razones que
en Ventas: oculta al solicitante que pidió algo indebido, y produce un informe
que dice ser de otra cuenta.

Tres departamentos más heredan este eje —Red Operativa por proveedor de flota,
Partners por partner, Soporte por cliente reportador—, así que un fallo aquí no
se queda aquí.
"""

from __future__ import annotations

import pytest

from core.informes.acotamiento import (
    ACOTADO_PROPIOS,
    ACOTADO_TODOS,
    AccesoDenegado,
    OrganizacionNoResuelta,
    resolver_organizacion,
)

AMPLIOS = ["Administrador", "DirectorEstrategia"]
ACOTADOS = ["Cliente", "Proveedor"]

USUARIO = 42
MI_CUENTA = 7
OTRA_CUENTA = 99

#: Pertenencia sembrada: el usuario 42 pertenece a la cuenta 7; nadie más tiene.
PERTENENCIA = {USUARIO: MI_CUENTA}


def _resolver(roles, cuenta_pedida=None, user_id=USUARIO, pertenencia=None):
    tabla = PERTENENCIA if pertenencia is None else pertenencia
    return resolver_organizacion(
        roles=roles,
        user_id=user_id,
        roles_amplios=AMPLIOS,
        roles_acotados=ACOTADOS,
        resolver_cuenta=tabla.get,
        cuenta_pedida=cuenta_pedida,
    )


class TestRolAmplio:
    @pytest.mark.parametrize("rol", AMPLIOS)
    def test_sin_cuenta_ve_todas(self, rol):
        acotamiento = _resolver([rol])

        assert acotamiento.titular is None
        assert acotamiento.alcance == ACOTADO_TODOS

    @pytest.mark.parametrize("rol", AMPLIOS)
    def test_con_cuenta_filtra_por_esa(self, rol):
        assert _resolver([rol], cuenta_pedida=OTRA_CUENTA).titular == OTRA_CUENTA

    def test_filtrar_no_reduce_su_alcance_declarado(self):
        acotamiento = _resolver(["Administrador"], cuenta_pedida=OTRA_CUENTA)

        assert acotamiento.alcance == ACOTADO_TODOS

    def test_no_necesita_pertenecer_a_ninguna_cuenta(self):
        # Un Administrador no es admin local de nada, y aun así ve todo.
        acotamiento = _resolver(["Administrador"], pertenencia={})

        assert acotamiento.titular is None


class TestRolAcotado:
    @pytest.mark.parametrize("rol", ACOTADOS)
    def test_sin_cuenta_queda_forzado_a_la_suya(self, rol):
        acotamiento = _resolver([rol])

        assert acotamiento.titular == MI_CUENTA
        assert acotamiento.alcance == ACOTADO_PROPIOS

    @pytest.mark.parametrize("rol", ACOTADOS)
    def test_pedir_la_suya_es_valido(self, rol):
        assert _resolver([rol], cuenta_pedida=MI_CUENTA).titular == MI_CUENTA

    @pytest.mark.parametrize("rol", ACOTADOS)
    def test_pedir_otra_es_negativa(self, rol):
        with pytest.raises(AccesoDenegado):
            _resolver([rol], cuenta_pedida=OTRA_CUENTA)

    @pytest.mark.parametrize("rol", ACOTADOS)
    def test_pedir_otra_no_devuelve_la_propia(self, rol):
        """La garantía central de research D1."""
        try:
            acotamiento = _resolver([rol], cuenta_pedida=OTRA_CUENTA)
        except AccesoDenegado:
            return  # comportamiento correcto

        pytest.fail(
            f"devolvio un acotamiento (cuenta={acotamiento.titular}) en vez de negar; "
            "sustituir la cuenta ajena por la propia oculta que se pidio algo indebido"
        )

    def test_el_acotamiento_es_la_cuenta_no_el_usuario(self):
        """El salto de indirección que distingue este eje del de «persona»."""
        acotamiento = _resolver(["Cliente"])

        assert acotamiento.titular == MI_CUENTA
        assert acotamiento.titular != USUARIO

    def test_la_cuenta_pedida_se_compara_como_entero(self):
        # `?cuenta=7` llega como texto desde la URL.
        assert _resolver(["Cliente"], cuenta_pedida="7").titular == MI_CUENTA


class TestSinCuentaResoluble:
    def test_un_rol_acotado_que_no_pertenece_a_ninguna_cuenta_es_negativa(self):
        with pytest.raises(OrganizacionNoResuelta):
            _resolver(["Cliente"], pertenencia={})

    def test_el_error_sigue_siendo_403_para_la_vista(self):
        # Hereda de `AccesoDenegado`: la vista no necesita distinguirlos.
        with pytest.raises(AccesoDenegado):
            _resolver(["Cliente"], pertenencia={})

    def test_se_resuelve_la_propia_antes_de_comparar_con_la_pedida(self):
        """Sin este orden, quien no tiene cuenta recibiría mensajes distintos
        según acertara o no el número de la ajena — un oráculo involuntario."""
        with pytest.raises(OrganizacionNoResuelta):
            _resolver(["Cliente"], cuenta_pedida=OTRA_CUENTA, pertenencia={})


class TestRolNoReconocido:
    @pytest.mark.parametrize(
        "roles", [[], None, ["Operador"], ["GerenteVentas"], ["Tecnico"]]
    )
    def test_siempre_negativa(self, roles):
        with pytest.raises(AccesoDenegado):
            _resolver(roles)

    def test_no_se_consulta_la_pertenencia_de_un_rol_ajeno(self):
        """Se descarta por rol antes de tocar el repositorio de cuentas."""
        llamadas = []

        def espia(uid):
            llamadas.append(uid)
            return MI_CUENTA

        with pytest.raises(AccesoDenegado):
            resolver_organizacion(
                roles=["Operador"],
                user_id=USUARIO,
                roles_amplios=AMPLIOS,
                roles_acotados=ACOTADOS,
                resolver_cuenta=espia,
            )

        assert llamadas == []


class TestRolesAcumulados:
    def test_amplio_mas_acotado_gana_el_amplio(self):
        acotamiento = _resolver(["Cliente", "Administrador"])

        assert acotamiento.titular is None
        assert acotamiento.alcance == ACOTADO_TODOS


class TestConfiguracionIncoherente:
    def test_un_rol_en_ambos_conjuntos_falla_al_configurar(self):
        with pytest.raises(ValueError, match="Cliente"):
            resolver_organizacion(
                roles=["Cliente"],
                user_id=USUARIO,
                roles_amplios=["Administrador", "Cliente"],
                roles_acotados=["Cliente"],
                resolver_cuenta=PERTENENCIA.get,
            )


class TestElEjePersonaNoSeToco:
    """research D1 — es una segunda función, no una reescritura."""

    def test_sigue_existiendo_y_funcionando(self):
        from core.informes.acotamiento import resolver

        acotamiento = resolver(
            roles=["GerenteVentas"],
            user_id=USUARIO,
            roles_amplios=["Administrador"],
            roles_acotados=["GerenteVentas"],
        )

        # El eje «persona» acota por el usuario, no por una cuenta.
        assert acotamiento.titular == USUARIO
