"""T008 — una cuenta suspendida **conserva** el acceso a sus propios registros (FR-011).

Es la diferencia deliberada con `ProveedorAccessService.resolve_cliente_activo`,
que exige cuenta `Activo`. Aquel controla **escrituras** —dar de alta unidades—
y ahí exigir una cuenta vigente tiene sentido. Éste controla la **lectura de los
propios registros**.

Negarle el acceso a quien tiene la cuenta suspendida lo dejaría **a ciegas sobre
su propia deuda**, justo cuando más necesita verla: el listado de facturas es
donde descubre qué tiene que regularizar para que le reactiven el servicio.
Sería un fallo de producto disfrazado de rigor de seguridad.
"""

from __future__ import annotations

import pytest

from core.informes.acotamiento import ACOTADO_PROPIOS, resolver_organizacion

AMPLIOS = ["Administrador"]
ACOTADOS = ["Cliente", "Proveedor"]

USUARIO = 55
SU_CUENTA = 12


def _resolver(estado_cuenta: str):
    """El resolutor recibe la cuenta ya resuelta; el estado no interviene.

    Que el estado se pase aquí es solo para hacer explícito en la prueba **qué
    situación se está simulando**: la función no lo mira, y eso es exactamente
    lo que se está verificando.
    """
    del estado_cuenta
    return resolver_organizacion(
        roles=["Cliente"],
        user_id=USUARIO,
        roles_amplios=AMPLIOS,
        roles_acotados=ACOTADOS,
        resolver_cuenta=lambda uid: SU_CUENTA if uid == USUARIO else None,
    )


class TestLaCuentaNoVigenteConservaElAcceso:
    @pytest.mark.parametrize(
        "estado", ["Activo", "Pendiente", "Rechazado", "Dado de baja"]
    )
    def test_sea_cual_sea_su_estado(self, estado):
        acotamiento = _resolver(estado)

        assert acotamiento.titular == SU_CUENTA
        assert acotamiento.alcance == ACOTADO_PROPIOS

    def test_una_cuenta_dada_de_baja_sigue_viendo_lo_suyo(self):
        # Es donde ve qué quedó pendiente al cerrar.
        assert _resolver("Dado de baja").titular == SU_CUENTA


class TestElResolutorNoConsultaElEstado:
    """La garantía estructural: la función no puede depender de algo que no ve."""

    def test_solo_recibe_el_identificador_de_usuario(self):
        recibidos = []

        resolver_organizacion(
            roles=["Cliente"],
            user_id=USUARIO,
            roles_amplios=AMPLIOS,
            roles_acotados=ACOTADOS,
            resolver_cuenta=lambda uid: recibidos.append(uid) or SU_CUENTA,
        )

        assert recibidos == [USUARIO]

    def test_el_codigo_no_menciona_el_estado_de_la_cuenta(self):
        import inspect

        from core.informes import acotamiento

        fuente = inspect.getsource(acotamiento.resolver_organizacion)

        # Si algún día alguien añade una comprobación de estado aquí, esta
        # prueba lo caza antes de que un cliente suspendido pierda la vista de
        # su propia deuda.
        assert "Activo" not in fuente
        assert "estado" not in fuente.replace("estan declarados", "")


class TestSigueNegandoLoQueDebeNegar:
    """Conservar el acceso a lo propio no relaja nada más."""

    def test_quien_no_pertenece_a_ninguna_cuenta_sigue_sin_acceder(self):
        from core.informes.acotamiento import OrganizacionNoResuelta

        with pytest.raises(OrganizacionNoResuelta):
            resolver_organizacion(
                roles=["Cliente"],
                user_id=999,
                roles_amplios=AMPLIOS,
                roles_acotados=ACOTADOS,
                resolver_cuenta=lambda uid: None,
            )

    def test_pedir_otra_cuenta_sigue_siendo_negativa(self):
        from core.informes.acotamiento import AccesoDenegado

        with pytest.raises(AccesoDenegado):
            resolver_organizacion(
                roles=["Cliente"],
                user_id=USUARIO,
                roles_amplios=AMPLIOS,
                roles_acotados=ACOTADOS,
                resolver_cuenta=lambda uid: SU_CUENTA,
                cuenta_pedida=999,
            )
