"""T009 — unificar el criterio de pertenencia rompería la regla del contrato.

La regla dice que **un informe nunca es más amplio que la pantalla operativa del
mismo dato**. En Red Operativa, la pantalla de alta de unidades usa el criterio
**estricto**: `IsProveedorFlota` exige ser administrador local de la cuenta.

Si el listado táctico usara el criterio amplio, un empleado vinculado a la
empresa proveedora —al que la pantalla rechaza— **vería por informe la flota
completa de su organización**. Es exactamente la puerta trasera que la regla
existe para impedir, y la que casi se cuela en F18 con el rol de partner.

Esta prueba fija que ese acceso **no** se concede. No prueba una implementación:
prueba una decisión, y por eso mira también qué criterio declara el módulo.
"""

from __future__ import annotations

import inspect

import pytest

from conftest import PINOT_STORE
from core.informes.acotamiento import OrganizacionNoResuelta, resolver_organizacion
from core.informes.pertenencia import ADMIN_LOCAL, VINCULO_A_CUENTA, resolutor

CUENTA = 6801
ADMIN = 6901
EMPLEADO = 6902

AMPLIOS = ["Administrador", "DirectorTecnologico"]
ACOTADOS = ["Cliente", "Proveedor"]


@pytest.fixture
def proveedor_con_empleado(mock_pinot):
    PINOT_STORE["Dim_Cliente"].append(
        {
            "idcliente": CUENTA, "razon_social": "Flota Austral Ltda.",
            "tipo": "Proveedor", "estado": "Activo", "admin_local_id": ADMIN,
            "fecha_creacion": 0, "fecha_actualizacion": 0,
        }
    )
    PINOT_STORE["Dim_Usuario_Cliente"].append(
        {"idusuario": EMPLEADO, "idcliente": CUENTA, "activo": True,
         "fecha_actualizacion": 0}
    )


class TestLaPantallaOperativaRechazaAlEmpleado:
    """El punto de partida: qué hace hoy la pantalla de alta de unidades."""

    def test_is_proveedor_flota_exige_administrador_local(self):
        from apps.red_operativa.permissions import IsProveedorFlota

        fuente = inspect.getsource(IsProveedorFlota)

        # Resuelve por `resolve_cliente_activo`, que va por `find_by_admin_local`.
        assert "resolve_cliente_activo" in fuente

    def test_y_el_empleado_no_resuelve_por_ese_criterio(self, proveedor_con_empleado):
        assert resolutor(ADMIN_LOCAL)(EMPLEADO) is None


class TestElListadoNoAmpliaEseAcceso:
    def test_el_empleado_recibe_negativa_en_el_criterio_de_este_modulo(
        self, proveedor_con_empleado
    ):
        from apps.red_operativa.views.informes_base import CRITERIO_PERTENENCIA

        with pytest.raises(OrganizacionNoResuelta):
            resolver_organizacion(
                roles=["Proveedor"],
                user_id=EMPLEADO,
                roles_amplios=AMPLIOS,
                roles_acotados=ACOTADOS,
                criterio=CRITERIO_PERTENENCIA,
            )

    def test_el_modulo_declara_el_criterio_estricto(self):
        from apps.red_operativa.views.informes_base import CRITERIO_PERTENENCIA

        assert CRITERIO_PERTENENCIA == ADMIN_LOCAL, (
            "usar el criterio amplio daria por informe la flota completa a un "
            "empleado que la pantalla de alta de unidades rechaza"
        )

    def test_el_administrador_local_si_accede(self, proveedor_con_empleado):
        from apps.red_operativa.views.informes_base import CRITERIO_PERTENENCIA

        acotamiento = resolver_organizacion(
            roles=["Proveedor"],
            user_id=ADMIN,
            roles_amplios=AMPLIOS,
            roles_acotados=ACOTADOS,
            criterio=CRITERIO_PERTENENCIA,
        )

        assert acotamiento.titular == CUENTA


class TestLaDiferenciaEsReal:
    """Si los dos criterios coincidieran, esta prueba no demostraría nada."""

    def test_el_criterio_amplio_si_le_daria_acceso(self, proveedor_con_empleado):
        # Se comprueba para dejar constancia de **qué** se está evitando: no es
        # una precaución teórica, el otro criterio sí concede.
        acotamiento = resolver_organizacion(
            roles=["Proveedor"],
            user_id=EMPLEADO,
            roles_amplios=AMPLIOS,
            roles_acotados=ACOTADOS,
            criterio=VINCULO_A_CUENTA,
        )

        assert acotamiento.titular == CUENTA

    def test_y_por_eso_los_dos_criterios_no_se_pueden_unificar(
        self, proveedor_con_empleado
    ):
        estricto = resolutor(ADMIN_LOCAL)(EMPLEADO)
        amplio = resolutor(VINCULO_A_CUENTA)(EMPLEADO)

        assert estricto != amplio
