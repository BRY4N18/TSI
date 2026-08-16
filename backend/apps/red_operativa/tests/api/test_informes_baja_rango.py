"""T029 y T030 — rango opcional y acotamiento del listado de bajas.

`bajas-unidad` es de **hechos del período**: una baja ocurre en un instante.
Es, junto a `validaciones-region`, uno de los dos listados de este departamento
que aceptan rango; `flota` y `regiones` describen estados.

El acotamiento tiene aquí un salto extra: `Fact_BajaUnidad` **no guarda el
proveedor**, solo la unidad. Un proveedor solo puede ver las bajas de *sus*
unidades, y eso exige resolver sus unidades antes de consultar las bajas.
"""

from __future__ import annotations

import json

import pytest

from apps.red_operativa.tests.conftest import PROVEEDOR_A, PROVEEDOR_B

BASE = "/api/v1/informes/red-operativa"
RUTA = f"{BASE}/bajas-unidad"


@pytest.mark.api
class TestSinRango:
    def test_es_200_no_400(self, api_client, admin_auth_headers, bajas_sembradas):
        assert api_client.get(RUTA, **admin_auth_headers).status_code == 200

    def test_devuelve_el_historico_completo(
        self, api_client, admin_auth_headers, bajas_sembradas
    ):
        cuerpo = api_client.get(f"{RUTA}?limit=500", **admin_auth_headers).json()

        assert len(cuerpo["data"]) == 3

    def test_meta_no_declara_extremos_que_no_se_aplicaron(
        self, api_client, admin_auth_headers, bajas_sembradas
    ):
        cuerpo = api_client.get(RUTA, **admin_auth_headers).json()

        assert "desde" not in cuerpo["meta"]["filtros"]
        assert "hasta" not in cuerpo["meta"]["filtros"]


@pytest.mark.api
class TestConRango:
    def test_solo_desde_acota(self, api_client, admin_auth_headers, bajas_sembradas):
        # Bajas: hace 10, 3 y 1 días desde 2026-08-11.
        cuerpo = api_client.get(
            f"{RUTA}?desde=2026-08-05&limit=500", **admin_auth_headers
        ).json()

        assert len(cuerpo["data"]) == 2

    def test_solo_hasta_acota(self, api_client, admin_auth_headers, bajas_sembradas):
        cuerpo = api_client.get(
            f"{RUTA}?hasta=2026-08-05&limit=500", **admin_auth_headers
        ).json()

        assert len(cuerpo["data"]) == 1

    def test_ambos_extremos_acotan(self, api_client, admin_auth_headers, bajas_sembradas):
        cuerpo = api_client.get(
            f"{RUTA}?desde=2026-08-05&hasta=2026-08-09&limit=500", **admin_auth_headers
        ).json()

        assert len(cuerpo["data"]) == 1

    def test_los_extremos_viajan_en_meta(
        self, api_client, admin_auth_headers, bajas_sembradas
    ):
        cuerpo = api_client.get(
            f"{RUTA}?desde=2026-08-01&hasta=2026-08-31", **admin_auth_headers
        ).json()

        assert cuerpo["meta"]["filtros"]["desde"] == "2026-08-01"
        assert cuerpo["meta"]["filtros"]["hasta"] == "2026-08-31"

    def test_rango_invertido_es_400(self, api_client, admin_auth_headers):
        respuesta = api_client.get(
            f"{RUTA}?desde=2026-08-31&hasta=2026-08-01", **admin_auth_headers
        )

        assert respuesta.status_code == 400


@pytest.mark.api
class TestQuienAceptaRangoYQuienNo:
    @pytest.mark.parametrize("informe", ["flota", "regiones"])
    def test_los_de_estado_actual_lo_rechazan(
        self, api_client, admin_auth_headers, informe
    ):
        respuesta = api_client.get(
            f"{BASE}/{informe}?desde=2026-08-01", **admin_auth_headers
        )

        assert respuesta.status_code == 400

    @pytest.mark.parametrize("informe", ["bajas-unidad", "validaciones-region"])
    def test_los_de_hechos_del_periodo_lo_aceptan(
        self, api_client, admin_auth_headers, informe
    ):
        respuesta = api_client.get(
            f"{BASE}/{informe}?desde=2026-08-01", **admin_auth_headers
        )

        assert respuesta.status_code == 200


@pytest.mark.api
class TestAcotamientoPorProveedorDeLaUnidad:
    """`Fact_BajaUnidad` no guarda el proveedor: se resuelve vía la unidad."""

    def test_el_proveedor_ve_las_bajas_de_sus_unidades(
        self, api_client, proveedor_a_headers, bajas_sembradas
    ):
        cuerpo = api_client.get(f"{RUTA}?limit=500", **proveedor_a_headers).json()

        assert {f["placa"] for f in cuerpo["data"]} == {"GRUA-01", "BAJA-01"}

    def test_y_no_las_de_otro(self, api_client, proveedor_a_headers, bajas_sembradas):
        cuerpo = api_client.get(f"{RUTA}?limit=500", **proveedor_a_headers).json()

        assert "AJENA-01" not in {f["placa"] for f in cuerpo["data"]}

    def test_el_otro_proveedor_ve_la_suya(
        self, api_client, proveedor_b_headers, bajas_sembradas
    ):
        cuerpo = api_client.get(f"{RUTA}?limit=500", **proveedor_b_headers).json()

        assert {f["placa"] for f in cuerpo["data"]} == {"AJENA-01"}

    def test_declara_que_esta_acotado(
        self, api_client, proveedor_a_headers, bajas_sembradas
    ):
        cuerpo = api_client.get(RUTA, **proveedor_a_headers).json()

        assert cuerpo["meta"]["acotado_a"] == "propios"

    def test_pedir_las_de_otro_es_403(
        self, api_client, proveedor_a_headers, bajas_sembradas
    ):
        respuesta = api_client.get(
            f"{RUTA}?proveedor={PROVEEDOR_B}", **proveedor_a_headers
        )

        assert respuesta.status_code == 403
        assert "data" not in json.loads(respuesta.content)

    def test_un_proveedor_sin_unidades_obtiene_lista_vacia(
        self, api_client, admin_auth_headers, bajas_sembradas
    ):
        # No es un error: es que no tiene unidades, así que no tiene bajas.
        cuerpo = api_client.get(f"{RUTA}?proveedor=999999", **admin_auth_headers).json()

        assert cuerpo["data"] == []

    def test_el_administrador_ve_las_de_todos(
        self, api_client, admin_auth_headers, bajas_sembradas
    ):
        cuerpo = api_client.get(f"{RUTA}?limit=500", **admin_auth_headers).json()

        assert {"GRUA-01", "AJENA-01"} <= {f["placa"] for f in cuerpo["data"]}


@pytest.mark.api
class TestFiltroDeTipo:
    def test_un_tipo_inexistente_es_400_nombrando_los_validos(
        self, api_client, admin_auth_headers
    ):
        cuerpo = api_client.get(
            f"{RUTA}?tipo_baja=Inventada", **admin_auth_headers
        ).json()

        assert cuerpo["error"] == "bad_request"
        assert "Normal" in cuerpo["detail"]

    def test_el_tipo_normal_acota(self, api_client, admin_auth_headers, bajas_sembradas):
        cuerpo = api_client.get(
            f"{RUTA}?tipo_baja=Normal&limit=500", **admin_auth_headers
        ).json()

        assert all(f["tipo_baja"] == "Normal" for f in cuerpo["data"])
        # Y ninguna trae caso afectado: son salidas ordenadas.
        assert all("caso_afectado" not in f for f in cuerpo["data"])
