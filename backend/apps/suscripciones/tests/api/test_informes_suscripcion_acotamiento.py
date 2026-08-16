"""T018 — acotamiento por organización, con **dos cuentas pobladas** (SC-001).

Es el detalle que hace real esta prueba. Con una sola cuenta, filtrar y no
filtrar devuelven lo mismo, así que pasaría aunque el acotamiento no existiera.

Y aquí el eje tiene un salto que el de Ventas no tenía: **el usuario pregunta y
el resultado se acota a la cuenta a la que pertenece**, no a él mismo.
"""

from __future__ import annotations

import pytest

from apps.suscripciones.tests.conftest import CUENTA_A, CUENTA_B

RUTA = "/api/v1/informes/suscripciones-facturacion/suscripciones"


@pytest.mark.api
class TestElClienteSoloVeSuCuenta:
    def test_obtiene_las_suyas(self, api_client, cliente_a_headers, dos_cuentas):
        cuerpo = api_client.get(RUTA, **cliente_a_headers).json()

        assert {f["cuenta"] for f in cuerpo["data"]} == {"Aseguradora Torres S.A."}

    def test_y_ninguna_de_la_otra(self, api_client, cliente_a_headers, dos_cuentas):
        cuerpo = api_client.get(RUTA, **cliente_a_headers).json()

        assert "Transportes Beltran Ltda." not in {f["cuenta"] for f in cuerpo["data"]}

    def test_declara_que_esta_acotado(self, api_client, cliente_a_headers, dos_cuentas):
        cuerpo = api_client.get(RUTA, **cliente_a_headers).json()

        assert cuerpo["meta"]["acotado_a"] == "propios"

    def test_las_dos_cuentas_son_disjuntas(
        self, api_client, cliente_a_headers, cliente_b_headers, dos_cuentas
    ):
        a = {f["cuenta"] for f in api_client.get(RUTA, **cliente_a_headers).json()["data"]}
        b = {f["cuenta"] for f in api_client.get(RUTA, **cliente_b_headers).json()["data"]}

        assert not (a & b)


@pytest.mark.api
class TestLaCuentaSuspendidaConservaSuVista:
    """FR-011 — es donde ve qué debe regularizar."""

    def test_accede_a_lo_suyo(self, api_client, cliente_b_headers, dos_cuentas):
        respuesta = api_client.get(RUTA, **cliente_b_headers)

        assert respuesta.status_code == 200
        assert {f["cuenta"] for f in respuesta.json()["data"]} == {
            "Transportes Beltran Ltda."
        }

    def test_y_sigue_sin_ver_la_ajena(self, api_client, cliente_b_headers, dos_cuentas):
        cuerpo = api_client.get(RUTA, **cliente_b_headers).json()

        assert "Aseguradora Torres S.A." not in {f["cuenta"] for f in cuerpo["data"]}


@pytest.mark.api
class TestElRolAmplioVeTodas:
    def test_el_administrador_ve_las_dos_cuentas(
        self, api_client, admin_auth_headers, dos_cuentas
    ):
        cuerpo = api_client.get(RUTA, **admin_auth_headers).json()

        cuentas = {f["cuenta"] for f in cuerpo["data"]}
        assert {"Aseguradora Torres S.A.", "Transportes Beltran Ltda."} <= cuentas

    def test_el_director_de_estrategia_tambien(
        self, api_client, director_estrategia_headers, dos_cuentas
    ):
        """§5.1 del SRS: Estrategia decide catálogo y precios."""
        cuerpo = api_client.get(RUTA, **director_estrategia_headers).json()

        cuentas = {f["cuenta"] for f in cuerpo["data"]}
        assert {"Aseguradora Torres S.A.", "Transportes Beltran Ltda."} <= cuentas

    def test_declara_alcance_total(self, api_client, admin_auth_headers, dos_cuentas):
        cuerpo = api_client.get(RUTA, **admin_auth_headers).json()

        assert cuerpo["meta"]["acotado_a"] == "todos"

    def test_el_conteo_del_cliente_es_estrictamente_menor(
        self, api_client, admin_auth_headers, cliente_a_headers, dos_cuentas
    ):
        """SC-001. Si fueran iguales, el acotamiento no estaría haciendo nada."""
        todas = api_client.get(RUTA, **admin_auth_headers).json()["data"]
        propias = api_client.get(RUTA, **cliente_a_headers).json()["data"]

        assert len(propias) < len(todas)

    def test_puede_filtrar_por_una_cuenta(
        self, api_client, admin_auth_headers, dos_cuentas
    ):
        cuerpo = api_client.get(f"{RUTA}?cuenta={CUENTA_B}", **admin_auth_headers).json()

        assert {f["cuenta"] for f in cuerpo["data"]} == {"Transportes Beltran Ltda."}

    def test_filtrar_no_reduce_su_alcance_declarado(
        self, api_client, admin_auth_headers, dos_cuentas
    ):
        cuerpo = api_client.get(f"{RUTA}?cuenta={CUENTA_A}", **admin_auth_headers).json()

        assert cuerpo["meta"]["acotado_a"] == "todos"


@pytest.mark.api
class TestElAcotamientoSobreviveALosFiltros:
    @pytest.mark.parametrize(
        "filtro", ["estado=Suspendida", "con_cambio_programado=false", "vence_en_dias=365"]
    )
    def test_ningun_filtro_deja_ver_la_cuenta_ajena(
        self, api_client, cliente_b_headers, dos_cuentas, filtro
    ):
        cuerpo = api_client.get(f"{RUTA}?{filtro}", **cliente_b_headers).json()

        assert "Aseguradora Torres S.A." not in {f["cuenta"] for f in cuerpo["data"]}

    def test_ni_siquiera_con_el_cursor(self, api_client, cliente_a_headers, dos_cuentas):
        primera = api_client.get(f"{RUTA}?limit=1", **cliente_a_headers).json()
        cursor = primera["meta"]["pagination"]["cursor"]

        segunda = api_client.get(
            f"{RUTA}?limit=1&cursor={cursor}", **cliente_a_headers
        ).json()

        for fila in primera["data"] + segunda["data"]:
            assert fila["cuenta"] == "Aseguradora Torres S.A."


@pytest.mark.api
class TestSinCuentaResoluble:
    def test_un_cliente_sin_cuenta_recibe_403(
        self, api_client, sin_cuenta_headers, dos_cuentas
    ):
        respuesta = api_client.get(RUTA, **sin_cuenta_headers)

        assert respuesta.status_code == 403

    def test_y_no_se_le_filtra_ninguna_fila(
        self, api_client, sin_cuenta_headers, dos_cuentas
    ):
        respuesta = api_client.get(RUTA, **sin_cuenta_headers)

        assert "Aseguradora" not in respuesta.content.decode()
