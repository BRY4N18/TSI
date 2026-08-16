"""T042 — `limit` sobre el máximo responde `400`, no se recorta en silencio (FR-018)."""

from __future__ import annotations

import pytest

BASE = "/api/v1/informes/ventas-crm"

LISTADOS = ["prospectos", "reasignaciones", "demos-activas", "notificaciones-enviadas"]


@pytest.mark.api
@pytest.mark.parametrize("informe", LISTADOS)
class TestLimite:
    def test_sobre_el_maximo_es_400(self, api_client, admin_auth_headers, informe):
        respuesta = api_client.get(f"{BASE}/{informe}?limit=5000", **admin_auth_headers)

        assert respuesta.status_code == 400

    def test_el_error_nombra_el_maximo(self, api_client, admin_auth_headers, informe):
        cuerpo = api_client.get(f"{BASE}/{informe}?limit=5000", **admin_auth_headers).json()

        assert "500" in cuerpo["detail"]

    def test_no_devuelve_datos_recortados(self, api_client, admin_auth_headers, informe):
        cuerpo = api_client.get(f"{BASE}/{informe}?limit=5000", **admin_auth_headers).json()

        assert "data" not in cuerpo, "un 400 no puede traer un listado recortado"

    def test_el_maximo_exacto_se_admite(self, api_client, admin_auth_headers, informe):
        respuesta = api_client.get(f"{BASE}/{informe}?limit=500", **admin_auth_headers)

        assert respuesta.status_code == 200

    def test_uno_mas_ya_es_400(self, api_client, admin_auth_headers, informe):
        respuesta = api_client.get(f"{BASE}/{informe}?limit=501", **admin_auth_headers)

        assert respuesta.status_code == 400

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
        # Interpretarlo como el defecto devolvería el listado al revés de como
        # el consumidor cree haberlo pedido.
        respuesta = api_client.get(f"{BASE}/{informe}?dir=arriba", **admin_auth_headers)

        assert respuesta.status_code == 400


@pytest.mark.api
class TestElLimitAcotaDeVerdad:
    def test_nunca_devuelve_mas_filas_que_el_limit(
        self, api_client, admin_auth_headers, dos_carteras
    ):
        # La consulta pide `limit + 1` para detectar la página siguiente; la
        # fila sobrante no puede escaparse a la respuesta.
        cuerpo = api_client.get(f"{BASE}/prospectos?limit=2", **admin_auth_headers).json()

        assert len(cuerpo["data"]) == 2
        assert cuerpo["meta"]["pagination"]["has_next"] is True

    def test_dir_desc_invierte_el_orden(
        self, api_client, admin_auth_headers, asignaciones_sembradas
    ):
        asc = api_client.get(
            f"{BASE}/reasignaciones?dir=asc", **admin_auth_headers
        ).json()["data"]
        desc = api_client.get(
            f"{BASE}/reasignaciones?dir=desc", **admin_auth_headers
        ).json()["data"]

        assert desc == list(reversed(asc))
