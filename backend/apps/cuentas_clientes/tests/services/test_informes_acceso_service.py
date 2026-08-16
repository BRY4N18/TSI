"""T020 — resolución de catálogos y forma de la fila.

Lo que el servicio garantiza y el repositorio no: que el consumidor reciba
**nombres y no identificadores**, que una ausencia se presente como ausencia, y
que el cursor se componga antes de recortar la fila —porque se construye con
columnas que la respuesta no lleva—.
"""

from __future__ import annotations

import pytest

from apps.cuentas_clientes.services.informes_acceso_service import InformesAccesoService


@pytest.fixture
def servicio(mock_pinot):
    return InformesAccesoService()


class TestResolucionDeCatalogos:
    def test_las_sesiones_devuelven_el_nombre_no_el_identificador(
        self, servicio, sesiones_sembradas
    ):
        pagina = servicio.sesiones_activas(limit=50)

        assert all(f["usuario"] for f in pagina.filas)
        assert all("idusuario" not in f for f in pagina.filas)

    def test_las_credenciales_devuelven_nombre_y_correo(
        self, servicio, credenciales_temporales_sembradas
    ):
        pagina = servicio.credenciales_temporales(limit=50)
        primera = pagina.filas[0]

        assert primera["usuario"] == "Admin Sistema"
        assert primera["gmail"] == "admin@tsi.com"

    def test_los_roles_llegan_como_nombre(self, servicio, usuario_multirol):
        pagina = servicio.usuarios_por_rol(limit=500)
        por_correo = {f["gmail"]: f for f in pagina.filas}

        assert por_correo["dosroles@tsi.com"]["roles"] == ["Auditor", "Revisor"]

    def test_los_accesos_tecnicos_traducen_las_dos_capas_de_rol(
        self, servicio, accesos_tecnicos_sembrados
    ):
        pagina = servicio.accesos_tecnicos(limit=50)
        por_cuenta = {f["usuario_servidor"]: f for f in pagina.filas}

        assert por_cuenta["admin_infra"]["roles_negocio"] == ["Administrador"]


class TestElCursorSeComponeAntesDeRecortarLaFila:
    """El cursor usa columnas que la respuesta no lleva; el orden importa."""

    def test_el_cursor_de_credenciales_usa_una_columna_que_no_se_devuelve(
        self, servicio, credenciales_temporales_sembradas
    ):
        pagina = servicio.credenciales_temporales(limit=2)

        assert pagina.has_next is True
        assert pagina.cursor is not None
        # `fecha_actualizacion|idcredencial`: ninguna de las dos está en la fila.
        assert "|" in pagina.cursor
        assert "idcredencial" not in pagina.filas[0]

    def test_el_cursor_de_sesiones_permite_recorrer_sin_repetir(
        self, servicio, sesiones_sembradas
    ):
        from core.repositories.cuentas_clientes.informes_acceso_repository import (
            CURSOR_SESIONES,
        )

        primera = servicio.sesiones_activas(limit=1)
        arranque = CURSOR_SESIONES.decodificar(primera.cursor)
        segunda = servicio.sesiones_activas(limit=1, cursor=arranque)

        vistos = [f["usuario"] for f in primera.filas + segunda.filas]
        assert len(vistos) == len(set(vistos))


class TestAusenciaSePresentaComoAusencia:
    def test_una_fecha_ausente_no_se_convierte_en_la_epoca(
        self, servicio, mock_pinot
    ):
        from conftest import PINOT_STORE
        from core.pinot.tiempo import SIN_FECHA
        from core.repositories.cuentas_clientes.credential_repository import (
            ESTADO_CREDENCIAL_CAMBIO_PASSWORD,
        )

        PINOT_STORE["Dim_Credencial"].append(
            {
                "idcredencial": 6001,
                "idusuario": 1,
                "contrasena": "x",
                "estadocredencial": ESTADO_CREDENCIAL_CAMBIO_PASSWORD,
                "fecha_actualizacion": SIN_FECHA,
            }
        )

        pagina = servicio.credenciales_temporales(limit=50)
        fila = next(f for f in pagina.filas if f["usuario"] == "Admin Sistema")

        # `1970-01-01` sería una fecha creíble que nadie cuestionaría (FR-021).
        assert fila["fecha_solicitud_cambio"] is None

    def test_un_usuario_que_no_resuelve_no_omite_la_fila(self, servicio, mock_pinot):
        from conftest import PINOT_STORE
        from core.repositories.cuentas_clientes.session_repository import (
            ESTADO_SESION_ACTIVA,
        )

        PINOT_STORE["Fact_Session"].append(
            {
                "idsession": 6002,
                "idusuario": 99999,  # no existe en Dim_Usuarios
                "token": "x",
                "navegador": "Huérfana",
                "fechahorainiciosesion": 1_790_000_000_000,
                "estadosession": ESTADO_SESION_ACTIVA,
            }
        )

        pagina = servicio.sesiones_activas(limit=500)

        # Una sesión abierta de un usuario que no resuelve es justo la que hay
        # que revisar: omitirla la escondería.
        huerfana = next(f for f in pagina.filas if f["navegador"] == "Huérfana")
        assert huerfana["usuario"] == ""
