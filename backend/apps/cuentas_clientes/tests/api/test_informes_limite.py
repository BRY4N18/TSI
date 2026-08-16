"""T046 — `limit` sobre el máximo responde `400`, no se recorta en silencio.

Recortar callando es la opción cómoda y la peor: quien pide 5.000 filas y recibe
500 no tiene forma de saber que faltan 4.500. La respuesta es válida, el envelope
es correcto, `has_next` puede incluso ser `true`... y el consumidor concluye que
ese es el total. El `400` convierte un error silencioso en uno visible.
"""

from __future__ import annotations

import pytest

BASE = "/api/v1/informes/cuentas-clientes"

LISTADOS = [
    "usuarios-por-rol",
    "sesiones-activas",
    "credenciales-temporales",
    "accesos-tecnicos",
    "solicitudes-alta-pendientes",
    "onboarding-incompleto",
    "cuentas-por-estado",
    "transferencias-propiedad",
]


@pytest.mark.api
@pytest.mark.parametrize("informe", LISTADOS)
class TestLimite:
    def test_sobre_el_maximo_es_400(self, api_client, admin_auth_headers, informe):
        respuesta = api_client.get(f"{BASE}/{informe}?limit=5000", **admin_auth_headers)

        assert respuesta.status_code == 400

    def test_el_error_nombra_el_maximo(self, api_client, admin_auth_headers, informe):
        cuerpo = api_client.get(
            f"{BASE}/{informe}?limit=5000", **admin_auth_headers
        ).json()

        assert "500" in cuerpo["detail"]

    def test_no_devuelve_datos_recortados(self, api_client, admin_auth_headers, informe):
        cuerpo = api_client.get(
            f"{BASE}/{informe}?limit=5000", **admin_auth_headers
        ).json()

        assert "data" not in cuerpo, "un 400 no puede traer un listado recortado"

    def test_el_maximo_exacto_se_admite(self, api_client, admin_auth_headers, informe):
        respuesta = api_client.get(f"{BASE}/{informe}?limit=500", **admin_auth_headers)

        assert respuesta.status_code == 200

    def test_uno_mas_que_el_maximo_ya_es_400(self, api_client, admin_auth_headers, informe):
        respuesta = api_client.get(f"{BASE}/{informe}?limit=501", **admin_auth_headers)

        assert respuesta.status_code == 400

    @pytest.mark.parametrize("valor", ["0", "-5"])
    def test_no_positivo_es_400(self, api_client, admin_auth_headers, informe, valor):
        respuesta = api_client.get(f"{BASE}/{informe}?limit={valor}", **admin_auth_headers)

        assert respuesta.status_code == 400

    @pytest.mark.parametrize("valor", ["muchas", "50.5"])
    def test_no_entero_es_400(self, api_client, admin_auth_headers, informe, valor):
        respuesta = api_client.get(f"{BASE}/{informe}?limit={valor}", **admin_auth_headers)

        assert respuesta.status_code == 400

    def test_por_defecto_es_50(self, api_client, admin_auth_headers, informe):
        cuerpo = api_client.get(f"{BASE}/{informe}", **admin_auth_headers).json()

        assert cuerpo["meta"]["pagination"]["limit"] == 50

    def test_el_limit_aplicado_se_declara_en_meta(
        self, api_client, admin_auth_headers, informe
    ):
        cuerpo = api_client.get(f"{BASE}/{informe}?limit=7", **admin_auth_headers).json()

        assert cuerpo["meta"]["pagination"]["limit"] == 7


@pytest.mark.api
class TestElLimitAcotaDeVerdad:
    def test_nunca_devuelve_mas_filas_que_el_limit(
        self, api_client, admin_auth_headers, cuentas_sembradas
    ):
        # La consulta pide `limit + 1` para detectar la página siguiente; la
        # fila sobrante no puede escaparse a la respuesta.
        cuerpo = api_client.get(
            f"{BASE}/cuentas-por-estado?limit=2", **admin_auth_headers
        ).json()

        assert len(cuerpo["data"]) == 2
        assert cuerpo["meta"]["pagination"]["has_next"] is True


@pytest.mark.api
class TestDir:
    def test_desc_invierte_el_orden_por_defecto(
        self, api_client, admin_auth_headers, credenciales_temporales_sembradas
    ):
        asc = api_client.get(
            f"{BASE}/credenciales-temporales?dir=asc", **admin_auth_headers
        ).json()["data"]
        desc = api_client.get(
            f"{BASE}/credenciales-temporales?dir=desc", **admin_auth_headers
        ).json()["data"]

        assert desc == list(reversed(asc))

    def test_un_valor_distinto_de_asc_o_desc_es_400(self, api_client, admin_auth_headers):
        # Interpretarlo como el defecto devolvería el listado al revés de como
        # el consumidor cree haberlo pedido.
        respuesta = api_client.get(
            f"{BASE}/cuentas-por-estado?dir=arriba", **admin_auth_headers
        )

        assert respuesta.status_code == 400
