"""T020 y T021 — acotamiento por proveedor, con **dos flotas pobladas** (SC-001, SC-002).

Con una sola flota, filtrar y no filtrar devuelven lo mismo y la prueba pasaría
aunque el acotamiento no existiera.

Incluye además el caso que distingue este módulo de Suscripciones: **un empleado
vinculado al proveedor pero que no es su administrador local recibe `403`**. Es
el criterio estricto, el mismo que exige la pantalla operativa de alta de
unidades — un informe no puede ser más amplio que su pantalla.
"""

from __future__ import annotations

import json

import pytest

from apps.red_operativa.tests.conftest import PROVEEDOR_A, PROVEEDOR_B

RUTA = "/api/v1/informes/red-operativa/flota"


@pytest.mark.api
class TestElProveedorSoloVeSuFlota:
    def test_obtiene_las_suyas(self, api_client, proveedor_a_headers, dos_flotas):
        cuerpo = api_client.get(f"{RUTA}?limit=500", **proveedor_a_headers).json()

        assert {f["placa"] for f in cuerpo["data"]} == {
            "GRUA-01", "FUERA-01", "BAJA-01",
        }

    def test_y_ninguna_del_otro(self, api_client, proveedor_a_headers, dos_flotas):
        cuerpo = api_client.get(f"{RUTA}?limit=500", **proveedor_a_headers).json()

        assert "AJENA-01" not in {f["placa"] for f in cuerpo["data"]}

    def test_declara_que_esta_acotado(self, api_client, proveedor_a_headers, dos_flotas):
        cuerpo = api_client.get(RUTA, **proveedor_a_headers).json()

        assert cuerpo["meta"]["acotado_a"] == "propios"

    def test_las_dos_flotas_son_disjuntas(
        self, api_client, proveedor_a_headers, proveedor_b_headers, dos_flotas
    ):
        a = {f["placa"] for f in api_client.get(f"{RUTA}?limit=500", **proveedor_a_headers).json()["data"]}
        b = {f["placa"] for f in api_client.get(f"{RUTA}?limit=500", **proveedor_b_headers).json()["data"]}

        assert not (a & b)


@pytest.mark.api
class TestElRolAmplioVeTodo:
    def test_el_administrador_ve_las_dos_flotas(
        self, api_client, admin_auth_headers, dos_flotas
    ):
        cuerpo = api_client.get(f"{RUTA}?limit=500", **admin_auth_headers).json()

        assert {"GRUA-01", "AJENA-01"} <= {f["placa"] for f in cuerpo["data"]}

    def test_el_director_de_expansion_tambien(
        self, api_client, director_expansion_headers, dos_flotas
    ):
        """§5.1 del SRS: Expansión decide dónde crecer, y necesita ver la red."""
        cuerpo = api_client.get(f"{RUTA}?limit=500", **director_expansion_headers).json()

        assert {"GRUA-01", "AJENA-01"} <= {f["placa"] for f in cuerpo["data"]}

    def test_declara_alcance_total(self, api_client, admin_auth_headers, dos_flotas):
        cuerpo = api_client.get(RUTA, **admin_auth_headers).json()

        assert cuerpo["meta"]["acotado_a"] == "todos"

    def test_el_conteo_del_proveedor_es_estrictamente_menor(
        self, api_client, admin_auth_headers, proveedor_a_headers, dos_flotas
    ):
        """SC-001. Si fueran iguales, el acotamiento no haría nada."""
        todas = api_client.get(f"{RUTA}?limit=500", **admin_auth_headers).json()["data"]
        propias = api_client.get(f"{RUTA}?limit=500", **proveedor_a_headers).json()["data"]

        assert len(propias) < len(todas)

    def test_puede_filtrar_por_un_proveedor(
        self, api_client, admin_auth_headers, dos_flotas
    ):
        cuerpo = api_client.get(
            f"{RUTA}?proveedor={PROVEEDOR_B}&limit=500", **admin_auth_headers
        ).json()

        assert {f["placa"] for f in cuerpo["data"]} == {"AJENA-01"}


@pytest.mark.api
class TestPedirLaFlotaAjena:
    """T021 — `403` sin devolver filas (SC-002)."""

    def test_responde_403(self, api_client, proveedor_a_headers, dos_flotas):
        respuesta = api_client.get(f"{RUTA}?proveedor={PROVEEDOR_B}", **proveedor_a_headers)

        assert respuesta.status_code == 403

    def test_no_devuelve_ninguna_fila(self, api_client, proveedor_a_headers, dos_flotas):
        respuesta = api_client.get(f"{RUTA}?proveedor={PROVEEDOR_B}", **proveedor_a_headers)

        assert "data" not in json.loads(respuesta.content)

    def test_no_devuelve_la_propia_disfrazada(
        self, api_client, proveedor_a_headers, dos_flotas
    ):
        respuesta = api_client.get(f"{RUTA}?proveedor={PROVEEDOR_B}", **proveedor_a_headers)

        assert "GRUA-01" not in respuesta.content.decode()

    def test_pedirse_a_si_mismo_es_valido(
        self, api_client, proveedor_a_headers, dos_flotas
    ):
        respuesta = api_client.get(
            f"{RUTA}?proveedor={PROVEEDOR_A}&limit=500", **proveedor_a_headers
        )

        assert respuesta.status_code == 200
        assert len(respuesta.json()["data"]) == 3


@pytest.mark.api
class TestElCriterioEstricto:
    """La diferencia con Suscripciones: aquí el vínculo no basta."""

    def test_un_empleado_vinculado_recibe_403(
        self, api_client, empleado_a_headers, dos_flotas
    ):
        respuesta = api_client.get(RUTA, **empleado_a_headers)

        assert respuesta.status_code == 403, (
            "el criterio amplio daria por informe la flota completa a un empleado "
            "que la pantalla de alta de unidades rechaza"
        )

    def test_y_no_se_le_filtra_ninguna_placa(
        self, api_client, empleado_a_headers, dos_flotas
    ):
        respuesta = api_client.get(RUTA, **empleado_a_headers)

        assert "GRUA-01" not in respuesta.content.decode()

    def test_el_administrador_local_del_mismo_proveedor_si_accede(
        self, api_client, proveedor_a_headers, dos_flotas
    ):
        assert api_client.get(RUTA, **proveedor_a_headers).status_code == 200


@pytest.mark.api
class TestElAcotamientoSobreviveALosFiltros:
    @pytest.mark.parametrize("filtro", ["dado_de_alta=true", "tipo_unidad=Grua"])
    def test_ningun_filtro_deja_ver_la_flota_ajena(
        self, api_client, proveedor_b_headers, dos_flotas, filtro
    ):
        cuerpo = api_client.get(f"{RUTA}?{filtro}&limit=500", **proveedor_b_headers).json()

        assert not ({f["placa"] for f in cuerpo["data"]} & {"GRUA-01", "FUERA-01"})

    def test_ni_siquiera_con_el_cursor(
        self, api_client, proveedor_a_headers, dos_flotas
    ):
        primera = api_client.get(f"{RUTA}?limit=1", **proveedor_a_headers).json()
        cursor = primera["meta"]["pagination"]["cursor"]

        segunda = api_client.get(
            f"{RUTA}?limit=1&cursor={cursor}", **proveedor_a_headers
        ).json()

        for fila in primera["data"] + segunda["data"]:
            assert fila["placa"] != "AJENA-01"
