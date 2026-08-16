"""T042 — `limit` sobre el máximo responde `400`, no se recorta en silencio (FR-019)."""

from __future__ import annotations

import pytest

BASE = "/api/v1/informes/suscripciones-facturacion"

LISTADOS = ["suscripciones", "facturas", "metodos-pago", "solicitudes-cambio-plan"]


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
        assert api_client.get(
            f"{BASE}/{informe}?limit=500", **admin_auth_headers
        ).status_code == 200

    def test_uno_mas_ya_es_400(self, api_client, admin_auth_headers, informe):
        assert api_client.get(
            f"{BASE}/{informe}?limit=501", **admin_auth_headers
        ).status_code == 400

    @pytest.mark.parametrize("valor", ["0", "-5", "muchas", "50.5"])
    def test_valores_invalidos_son_400(
        self, api_client, admin_auth_headers, informe, valor
    ):
        respuesta = api_client.get(f"{BASE}/{informe}?limit={valor}", **admin_auth_headers)

        assert respuesta.status_code == 400

    def test_por_defecto_es_50(self, api_client, admin_auth_headers, informe):
        cuerpo = api_client.get(f"{BASE}/{informe}", **admin_auth_headers).json()

        assert cuerpo["meta"]["pagination"]["limit"] == 50

    def test_un_dir_invalido_es_400(self, api_client, admin_auth_headers, informe):
        respuesta = api_client.get(f"{BASE}/{informe}?dir=arriba", **admin_auth_headers)

        assert respuesta.status_code == 400


@pytest.mark.api
class TestElLimitAcotaDeVerdad:
    def test_nunca_devuelve_mas_filas_que_el_limit(
        self, api_client, admin_auth_headers, todo_sembrado
    ):
        # La consulta pide `limit + 1` para detectar la página siguiente; la
        # fila sobrante no puede escaparse a la respuesta.
        cuerpo = api_client.get(f"{BASE}/facturas?limit=2", **admin_auth_headers).json()

        assert len(cuerpo["data"]) == 2
        assert cuerpo["meta"]["pagination"]["has_next"] is True

    def test_dir_desc_invierte_el_orden(
        self, api_client, admin_auth_headers, todo_sembrado
    ):
        asc = api_client.get(
            f"{BASE}/solicitudes-cambio-plan?dir=asc&limit=500", **admin_auth_headers
        ).json()["data"]
        desc = api_client.get(
            f"{BASE}/solicitudes-cambio-plan?dir=desc&limit=500", **admin_auth_headers
        ).json()["data"]

        assert desc == list(reversed(asc))


@pytest.mark.api
class TestFiltrosInvalidos:
    def test_un_estado_de_suscripcion_inexistente_es_400(
        self, api_client, admin_auth_headers
    ):
        cuerpo = api_client.get(
            f"{BASE}/suscripciones?estado=Vigente", **admin_auth_headers
        ).json()

        assert cuerpo["error"] == "bad_request"
        assert "Activa" in cuerpo["detail"]

    def test_un_estado_de_pago_inexistente_es_400(self, api_client, admin_auth_headers):
        cuerpo = api_client.get(
            f"{BASE}/facturas?estado_pago=Impaga", **admin_auth_headers
        ).json()

        assert cuerpo["error"] == "bad_request"
        # Los cuatro valores reales, incluida la disputa.
        assert "En disputa" in cuerpo["detail"]

    def test_un_estado_de_solicitud_inexistente_es_400(
        self, api_client, admin_auth_headers
    ):
        cuerpo = api_client.get(
            f"{BASE}/solicitudes-cambio-plan?estado=Abierta", **admin_auth_headers
        ).json()

        assert "Pendiente" in cuerpo["detail"]

    def test_una_fecha_de_cancelacion_no_iso_es_400(self, api_client, admin_auth_headers):
        respuesta = api_client.get(
            f"{BASE}/suscripciones?cancelada_desde=ayer", **admin_auth_headers
        )

        assert respuesta.status_code == 400
