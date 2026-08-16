"""Decisión #23 — la pertenencia a una cuenta ya se puede escribir.

Hasta 2026-08-15 `Dim_Usuario_Cliente` no la escribía nadie: la tabla y su topic
estaban declarados, pero faltaba la entrada en `KAFKA_TOPICS`. Toda la
pertenencia se resolvía por el respaldo —`admin_local_id`— y de una organización
con cinco usuarios **solo uno** veía los datos de su cuenta.

Lo que estas pruebas fijan no es el `publish`: es **la consecuencia**. Vincular a
un usuario le abre la lectura en tres departamentos a la vez, y eso tiene que
verse en una prueba, no solo en un comentario.
"""

from __future__ import annotations

import pytest

from conftest import PINOT_STORE

CUENTA = 8801
ADMIN_LOCAL = 8901
EMPLEADO = 8902  # vinculado, pero NO administrador local


@pytest.fixture
def organizacion(mock_pinot, mock_kafka):
    PINOT_STORE["Dim_Usuarios"].extend(
        [
            {"idusuario": ADMIN_LOCAL, "nombres": "Ana", "apellidos": "Duarte",
             "gmail": "ana.duarte@empresa.com", "activo": True,
             "fecha_actualizacion": 1},
            {"idusuario": EMPLEADO, "nombres": "Luis", "apellidos": "Peralta",
             "gmail": "luis.peralta@empresa.com", "activo": True,
             "fecha_actualizacion": 1},
        ]
    )
    PINOT_STORE["Dim_Cliente"].append(
        {"idcliente": CUENTA, "razon_social": "Empresa Duarte S.A.",
         "tipo": "Corporativo", "estado": "Activo",
         "admin_local_id": ADMIN_LOCAL,
         "fecha_creacion": 1, "fecha_actualizacion": 1}
    )


@pytest.mark.django_db
class TestElTopicExiste:
    def test_kafka_topics_declara_el_topic_de_vinculos(self):
        """Era lo único que faltaba: la tabla y el topic ya estaban declarados
        en `database/tablas.json` desde el principio."""
        from django.conf import settings

        assert settings.KAFKA_TOPICS["usuario_cliente"] == "Dim_Usuario_Cliente_topic"

    def test_el_repositorio_publica_el_vinculo(self, organizacion, mock_kafka):
        from core.repositories.cuentas_clientes.cuenta_usuario_repository import (
            CuentaUsuarioRepository,
        )

        repo = CuentaUsuarioRepository()
        payload = repo.vincular(EMPLEADO, CUENTA)

        assert payload["idusuario"] == EMPLEADO
        assert payload["idcliente"] == CUENTA
        assert payload["activo"] is True

    def test_desvincular_marca_inactivo_en_vez_de_borrar(
        self, organizacion, mock_kafka
    ):
        """Borrar haría indistinguible «nunca perteneció» de «se le retiró»."""
        from core.repositories.cuentas_clientes.cuenta_usuario_repository import (
            CuentaUsuarioRepository,
        )

        payload = CuentaUsuarioRepository().desvincular(EMPLEADO, CUENTA)

        assert payload["activo"] is False


@pytest.mark.django_db
class TestLaConsecuenciaReal:
    """Lo que decidió la #23: un empleado vinculado ve los datos de su cuenta."""

    def test_sin_vinculo_un_empleado_no_resuelve_ninguna_cuenta(self, organizacion):
        """Es el estado en que estaba **todo el sistema** hasta ahora."""
        from core.informes.pertenencia import por_vinculo_a_cuenta

        assert por_vinculo_a_cuenta(EMPLEADO) is None

    def test_con_vinculo_el_empleado_resuelve_su_cuenta(self, organizacion):
        PINOT_STORE["Dim_Usuario_Cliente"].append(
            {"idusuario": EMPLEADO, "idcliente": CUENTA, "activo": True}
        )

        from core.informes.pertenencia import por_vinculo_a_cuenta

        assert por_vinculo_a_cuenta(EMPLEADO) == CUENTA

    def test_el_criterio_estricto_sigue_sin_reconocerlo(self, organizacion):
        """⚠️ El vínculo **no** convierte a nadie en administrador local.

        Red Operativa y Suscripciones acotan por el criterio estricto porque sus
        pantallas operativas lo hacen: dar de alta unidades y ver la facturación
        siguen siendo del administrador. Si el vínculo los ampliara, este cambio
        habría abierto una puerta trasera en dos departamentos que no la pidieron.
        """
        PINOT_STORE["Dim_Usuario_Cliente"].append(
            {"idusuario": EMPLEADO, "idcliente": CUENTA, "activo": True}
        )

        from core.informes.pertenencia import por_admin_local, por_vinculo_a_cuenta

        assert por_vinculo_a_cuenta(EMPLEADO) == CUENTA
        assert por_admin_local(EMPLEADO) is None
        assert por_admin_local(ADMIN_LOCAL) == CUENTA

    def test_un_vinculo_retirado_deja_de_dar_acceso(self, organizacion):
        PINOT_STORE["Dim_Usuario_Cliente"].append(
            {"idusuario": EMPLEADO, "idcliente": CUENTA, "activo": False}
        )

        from core.informes.pertenencia import por_vinculo_a_cuenta

        assert por_vinculo_a_cuenta(EMPLEADO) is None

    def test_el_administrador_local_sigue_resolviendo_sin_fila_de_vinculo(
        self, organizacion
    ):
        """El respaldo **se conserva**: las cuentas anteriores a este cambio no
        tienen filas de vínculo, y quitarlo dejaría fuera a sus administradores.
        Por eso no hace falta migrar nada.
        """
        from core.informes.pertenencia import por_vinculo_a_cuenta

        assert por_vinculo_a_cuenta(ADMIN_LOCAL) == CUENTA


@pytest.mark.django_db
class TestElAltaDeUsuarioLoDeclara:
    def test_crear_un_usuario_con_cuenta_lo_vincula(self, organizacion, mock_kafka):
        from apps.cuentas_clientes.services.user_management_service import (
            UserManagementService,
        )

        vinculos: list[tuple[int, int]] = []

        class _RepoFalso:
            def vincular(self, user_id, cliente_id):
                vinculos.append((user_id, cliente_id))
                return {}

        servicio = UserManagementService(cuenta_usuario_repo=_RepoFalso())
        usuario = servicio.create_user(
            {
                "nombres": "Marta", "apellidos": "Cano",
                "gmail": "marta.cano@empresa.com", "idcliente": CUENTA,
            },
            admin_roles=["Administrador"],
        )

        assert vinculos == [(usuario["idusuario"], CUENTA)]

    def test_crear_un_usuario_sin_cuenta_no_vincula_nada(
        self, organizacion, mock_kafka
    ):
        """Los usuarios internos de TSI no pertenecen a ninguna organización.

        Exigir la cuenta dejaría sin poder crearlos, así que el campo es
        **opcional** — y su ausencia no vincula a una cuenta por defecto.
        """
        from apps.cuentas_clientes.services.user_management_service import (
            UserManagementService,
        )

        class _RepoQueNoDebeLlamarse:
            def vincular(self, *_a, **_k):
                raise AssertionError("no debe vincularse sin idcliente")

        servicio = UserManagementService(
            cuenta_usuario_repo=_RepoQueNoDebeLlamarse()
        )
        usuario = servicio.create_user(
            {"nombres": "Op", "apellidos": "Interno", "gmail": "op@tsi.com"},
            admin_roles=["Administrador"],
        )

        assert "idcliente" not in usuario
