"""T008 — el criterio de pertenencia es un parámetro, no una constante (research D1).

«Pertenecer a una cuenta» significa **dos cosas distintas** en este sistema:

* **estricto** — ser su administrador local: una sola persona por cuenta;
* **amplio** — estar vinculado a ella: cualquier miembro.

Ambos casos se prueban **sobre los mismos datos**, que es lo único que demuestra
que el criterio es de verdad una opción y no una etiqueta: un empleado vinculado
pero no administrador resuelve con uno y recibe negativa con el otro.
"""

from __future__ import annotations

import pytest

from conftest import PINOT_STORE
from core.informes.acotamiento import (
    ACOTADO_PROPIOS,
    AccesoDenegado,
    OrganizacionNoResuelta,
    resolver_organizacion,
)
from core.informes.pertenencia import (
    ADMIN_LOCAL,
    CRITERIOS,
    VINCULO_A_CUENTA,
    resolutor,
)

CUENTA = 6601
ADMIN = 6701      # administrador local de la cuenta
EMPLEADO = 6702   # vinculado a la cuenta, pero NO su administrador

AMPLIOS = ["Administrador"]
ACOTADOS = ["Cliente", "Proveedor"]


@pytest.fixture
def cuenta_con_empleado(mock_pinot):
    """Una cuenta, su administrador local y un empleado vinculado."""
    PINOT_STORE["Dim_Cliente"].append(
        {
            "idcliente": CUENTA, "razon_social": "Gruas del Norte S.A.",
            "tipo": "Proveedor", "estado": "Activo", "admin_local_id": ADMIN,
            "fecha_creacion": 0, "fecha_actualizacion": 0,
        }
    )
    PINOT_STORE["Dim_Usuario_Cliente"].append(
        {"idusuario": EMPLEADO, "idcliente": CUENTA, "activo": True,
         "fecha_actualizacion": 0}
    )


def _resolver(user_id, criterio):
    return resolver_organizacion(
        roles=["Proveedor"],
        user_id=user_id,
        roles_amplios=AMPLIOS,
        roles_acotados=ACOTADOS,
        criterio=criterio,
    )


class TestCriterioEstricto:
    """`ADMIN_LOCAL` — el que usan Red Operativa y Suscripciones."""

    def test_el_administrador_local_resuelve(self, cuenta_con_empleado):
        acotamiento = _resolver(ADMIN, ADMIN_LOCAL)

        assert acotamiento.titular == CUENTA
        assert acotamiento.alcance == ACOTADO_PROPIOS

    def test_un_empleado_vinculado_recibe_negativa(self, cuenta_con_empleado):
        """Aunque pertenezca a la organización.

        Es lo correcto aquí: la pantalla operativa de alta de unidades también
        lo rechaza, y un informe no puede ser más amplio que su pantalla.
        """
        with pytest.raises(OrganizacionNoResuelta):
            _resolver(EMPLEADO, ADMIN_LOCAL)


class TestCriterioAmplio:
    """`VINCULO_A_CUENTA` — el que usarán Soporte y Seguimiento."""

    def test_el_empleado_vinculado_resuelve(self, cuenta_con_empleado):
        acotamiento = _resolver(EMPLEADO, VINCULO_A_CUENTA)

        assert acotamiento.titular == CUENTA

    def test_el_administrador_local_tambien(self, cuenta_con_empleado):
        """El criterio amplio **contiene** al estricto."""
        acotamiento = _resolver(ADMIN, VINCULO_A_CUENTA)

        assert acotamiento.titular == CUENTA


class TestLosDosCriteriosDifierenSobreLosMismosDatos:
    def test_el_empleado_es_el_caso_que_los_distingue(self, cuenta_con_empleado):
        """Si no difirieran, el parámetro sería decorativo."""
        assert resolutor(VINCULO_A_CUENTA)(EMPLEADO) == CUENTA
        assert resolutor(ADMIN_LOCAL)(EMPLEADO) is None

    def test_el_administrador_resuelve_igual_con_los_dos(self, cuenta_con_empleado):
        assert resolutor(ADMIN_LOCAL)(ADMIN) == CUENTA
        assert resolutor(VINCULO_A_CUENTA)(ADMIN) == CUENTA


class TestElDefectoNoCambio:
    """La ampliación añade una opción; no altera la existente."""

    def test_sin_declarar_criterio_se_usa_el_estricto(self, cuenta_con_empleado):
        # Es lo que Suscripciones hacía antes de que este parámetro existiera.
        acotamiento = resolver_organizacion(
            roles=["Cliente"],
            user_id=ADMIN,
            roles_amplios=AMPLIOS,
            roles_acotados=ACOTADOS,
        )

        assert acotamiento.titular == CUENTA

    def test_y_el_empleado_sigue_sin_resolver_por_defecto(self, cuenta_con_empleado):
        with pytest.raises(OrganizacionNoResuelta):
            resolver_organizacion(
                roles=["Cliente"],
                user_id=EMPLEADO,
                roles_amplios=AMPLIOS,
                roles_acotados=ACOTADOS,
            )

    def test_suscripciones_declara_el_estricto(self):
        from apps.suscripciones.views.informes_base import CRITERIO_PERTENENCIA

        assert CRITERIO_PERTENENCIA == ADMIN_LOCAL


class TestConfiguracionIncoherente:
    def test_un_criterio_desconocido_falla_nombrando_los_validos(self):
        # Falla al configurar y no en tiempo de petición: un criterio mal
        # escrito resolvería a `None` para todos y devolvería 403 a usuarios
        # legítimos, que es mucho más difícil de diagnosticar.
        with pytest.raises(ValueError, match="admin_local"):
            resolutor("inventado")

    def test_declarar_criterio_y_resolutor_a_la_vez_falla(self, cuenta_con_empleado):
        with pytest.raises(ValueError, match="no ambos"):
            resolver_organizacion(
                roles=["Cliente"],
                user_id=ADMIN,
                roles_amplios=AMPLIOS,
                roles_acotados=ACOTADOS,
                criterio=ADMIN_LOCAL,
                resolver_cuenta=lambda uid: CUENTA,
            )

    def test_los_dos_criterios_estan_declarados(self):
        assert set(CRITERIOS) == {"admin_local", "vinculo"}


class TestLoQueNoCambia:
    """Parametrizar la pertenencia no relaja ninguna otra garantía."""

    def test_pedir_otra_cuenta_sigue_siendo_negativa(self, cuenta_con_empleado):
        with pytest.raises(AccesoDenegado):
            resolver_organizacion(
                roles=["Proveedor"],
                user_id=ADMIN,
                roles_amplios=AMPLIOS,
                roles_acotados=ACOTADOS,
                criterio=ADMIN_LOCAL,
                cuenta_pedida=999,
            )

    def test_el_rol_amplio_no_consulta_la_pertenencia(self, cuenta_con_empleado):
        # Un Administrador no es admin local de nada, y aun así ve todo.
        acotamiento = resolver_organizacion(
            roles=["Administrador"],
            user_id=999999,
            roles_amplios=AMPLIOS,
            roles_acotados=ACOTADOS,
            criterio=ADMIN_LOCAL,
        )

        assert acotamiento.titular is None
