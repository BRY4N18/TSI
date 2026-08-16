"""T019 — el acotamiento, probado con **dos carteras pobladas a la vez** (SC-001).

Es el detalle que hace real esta prueba. Con una sola cartera, filtrar por
ejecutivo y no filtrar devuelven exactamente lo mismo, así que la prueba pasaría
aunque el acotamiento no existiera. Los dos gerentes tienen cartera, y de
tamaños distintos, para que el conteo pueda distinguir un caso del otro.
"""

from __future__ import annotations

import pytest

RUTA = "/api/v1/informes/ventas-crm/prospectos"


@pytest.mark.api
class TestElGerenteSoloVeLoSuyo:
    def test_obtiene_sus_prospectos(self, api_client, gerente_a_headers, dos_carteras):
        cuerpo = api_client.get(RUTA, **gerente_a_headers).json()

        empresas = {f["empresa"] for f in cuerpo["data"]}
        assert empresas == {"Alfa Seguros", "Beta Logistica", "Gamma Municipal"}

    def test_y_cero_de_otro_ejecutivo(self, api_client, gerente_a_headers, dos_carteras):
        cuerpo = api_client.get(RUTA, **gerente_a_headers).json()

        empresas = {f["empresa"] for f in cuerpo["data"]}
        assert not (empresas & {"Delta Transportes", "Epsilon Flotas"}), (
            "el gerente A esta viendo prospectos del gerente B"
        )

    def test_el_otro_gerente_ve_los_suyos_y_solo_los_suyos(
        self, api_client, gerente_b_headers, dos_carteras
    ):
        cuerpo = api_client.get(RUTA, **gerente_b_headers).json()

        assert {f["empresa"] for f in cuerpo["data"]} == {
            "Delta Transportes",
            "Epsilon Flotas",
        }

    def test_las_dos_carteras_son_disjuntas(
        self, api_client, gerente_a_headers, gerente_b_headers, dos_carteras
    ):
        a = {f["empresa"] for f in api_client.get(RUTA, **gerente_a_headers).json()["data"]}
        b = {f["empresa"] for f in api_client.get(RUTA, **gerente_b_headers).json()["data"]}

        assert not (a & b)

    def test_declara_que_el_resultado_esta_acotado(
        self, api_client, gerente_a_headers, dos_carteras
    ):
        # Sin esto, «no hay prospectos perdidos» y «no hay perdidos míos» son
        # indistinguibles para quien consulta.
        cuerpo = api_client.get(RUTA, **gerente_a_headers).json()

        assert cuerpo["meta"]["acotado_a"] == "propios"


@pytest.mark.api
class TestElRolAmplioVeTodo:
    def test_el_administrador_obtiene_las_dos_carteras(
        self, api_client, admin_auth_headers, dos_carteras
    ):
        cuerpo = api_client.get(RUTA, **admin_auth_headers).json()

        empresas = {f["empresa"] for f in cuerpo["data"]}
        assert {"Alfa Seguros", "Delta Transportes"} <= empresas

    def test_el_director_de_marketing_tambien(
        self, api_client, director_marketing_headers, dos_carteras
    ):
        """§5.1 del SRS: la autoridad accede sin acotamiento por titularidad."""
        cuerpo = api_client.get(RUTA, **director_marketing_headers).json()

        empresas = {f["empresa"] for f in cuerpo["data"]}
        assert {"Alfa Seguros", "Delta Transportes"} <= empresas

    def test_declara_alcance_total(self, api_client, admin_auth_headers, dos_carteras):
        cuerpo = api_client.get(RUTA, **admin_auth_headers).json()

        assert cuerpo["meta"]["acotado_a"] == "todos"

    def test_el_conteo_del_gerente_es_estrictamente_menor(
        self, api_client, admin_auth_headers, gerente_a_headers, dos_carteras
    ):
        """SC-001. Si fueran iguales, el acotamiento no estaría haciendo nada."""
        todos = api_client.get(RUTA, **admin_auth_headers).json()["data"]
        propios = api_client.get(RUTA, **gerente_a_headers).json()["data"]

        assert len(propios) < len(todos)


@pytest.mark.api
class TestElRolAmplioPuedeFiltrar:
    def test_por_un_ejecutivo_concreto(self, api_client, admin_auth_headers, dos_carteras):
        from apps.ventas_crm.tests.conftest import GERENTE_B

        cuerpo = api_client.get(
            f"{RUTA}?ejecutivo={GERENTE_B}", **admin_auth_headers
        ).json()

        assert {f["empresa"] for f in cuerpo["data"]} == {
            "Delta Transportes",
            "Epsilon Flotas",
        }

    def test_filtrar_no_reduce_su_alcance_declarado(
        self, api_client, admin_auth_headers, dos_carteras
    ):
        # Sigue teniendo acceso a todo: ha elegido mirar a uno. Declararlo como
        # `propios` le haría creer que ve su propia cartera.
        from apps.ventas_crm.tests.conftest import GERENTE_B

        cuerpo = api_client.get(
            f"{RUTA}?ejecutivo={GERENTE_B}", **admin_auth_headers
        ).json()

        assert cuerpo["meta"]["acotado_a"] == "todos"

    def test_el_ejecutivo_aplicado_viaja_en_meta(
        self, api_client, admin_auth_headers, dos_carteras
    ):
        from apps.ventas_crm.tests.conftest import GERENTE_B

        cuerpo = api_client.get(
            f"{RUTA}?ejecutivo={GERENTE_B}", **admin_auth_headers
        ).json()

        assert cuerpo["meta"]["filtros"]["ejecutivo"] == GERENTE_B


@pytest.mark.api
class TestElAcotamientoSobreviveALosFiltros:
    """Combinar un filtro con el acotamiento no puede ensanchar el resultado."""

    @pytest.mark.parametrize("filtro", ["estado=activo", "etapa=Contactado", "canal=Web"])
    def test_ningun_filtro_deja_ver_cartera_ajena(
        self, api_client, gerente_b_headers, dos_carteras, filtro
    ):
        cuerpo = api_client.get(f"{RUTA}?{filtro}", **gerente_b_headers).json()

        empresas = {f["empresa"] for f in cuerpo["data"]}
        assert not (empresas & {"Alfa Seguros", "Beta Logistica", "Gamma Municipal"})

    def test_ni_siquiera_con_el_cursor(self, api_client, gerente_b_headers, dos_carteras):
        primera = api_client.get(f"{RUTA}?limit=1", **gerente_b_headers).json()
        cursor = primera["meta"]["pagination"]["cursor"]

        segunda = api_client.get(
            f"{RUTA}?limit=1&cursor={cursor}", **gerente_b_headers
        ).json()

        for fila in primera["data"] + segunda["data"]:
            assert fila["empresa"] in {"Delta Transportes", "Epsilon Flotas"}
