"""T042 y T043 — integridad de la paginación y `limit` que no se recorta (SC-007, FR-020)."""

from __future__ import annotations

import json
from urllib.parse import quote

import pytest

BASE = "/api/v1/informes/red-operativa"

LISTADOS = ["flota", "bajas-unidad", "regiones", "validaciones-region"]


def _recorrer(api_client, headers, informe, limit=1, tope=100):
    filas = []
    cursor = None
    paginas = 0
    while paginas < tope:
        url = f"{BASE}/{informe}?limit={limit}"
        if cursor:
            url += f"&cursor={quote(cursor)}"
        cuerpo = api_client.get(url, **headers).json()
        filas.extend(cuerpo["data"])
        paginas += 1
        cursor = cuerpo["meta"]["pagination"]["cursor"]
        if cursor is None:
            return filas, paginas
    raise AssertionError(f"'{informe}' no termino de paginar en {tope} paginas")


@pytest.fixture
def sembrado(todo_sembrado, regiones_sembradas):
    return True


@pytest.mark.api
@pytest.mark.parametrize("informe", LISTADOS)
class TestIntegridadDelRecorrido:
    def test_coincide_con_la_lectura_de_una_pagina(
        self, api_client, admin_auth_headers, informe, sembrado
    ):
        de_una_vez = api_client.get(
            f"{BASE}/{informe}?limit=500", **admin_auth_headers
        ).json()["data"]

        por_paginas, _ = _recorrer(api_client, admin_auth_headers, informe)

        assert por_paginas == de_una_vez, (
            "el recorrido por paginas no reproduce la lectura completa"
        )

    def test_ninguna_fila_se_repite(
        self, api_client, admin_auth_headers, informe, sembrado
    ):
        filas, _ = _recorrer(api_client, admin_auth_headers, informe)

        serializadas = [json.dumps(f, sort_keys=True) for f in filas]
        assert len(serializadas) == len(set(serializadas))

    def test_el_tamano_de_pagina_no_altera_el_contenido(
        self, api_client, admin_auth_headers, informe, sembrado
    ):
        de_una, _ = _recorrer(api_client, admin_auth_headers, informe, limit=1)
        de_dos, _ = _recorrer(api_client, admin_auth_headers, informe, limit=2)

        assert de_una == de_dos

    def test_el_recorrido_termina(
        self, api_client, admin_auth_headers, informe, sembrado
    ):
        filas, paginas = _recorrer(api_client, admin_auth_headers, informe)

        assert paginas == max(len(filas), 1)


@pytest.mark.api
class TestElRecorridoRespetaElAcotamiento:
    def test_paginando_no_se_cuela_flota_ajena(
        self, api_client, proveedor_b_headers, dos_flotas
    ):
        filas, _ = _recorrer(api_client, proveedor_b_headers, "flota")

        assert {f["placa"] for f in filas} == {"AJENA-01"}


@pytest.mark.api
@pytest.mark.parametrize("informe", LISTADOS)
class TestLimite:
    """T043 — sobre el máximo es `400`, no se recorta en silencio."""

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

        assert "data" not in cuerpo

    def test_el_maximo_exacto_se_admite(self, api_client, admin_auth_headers, informe):
        assert api_client.get(
            f"{BASE}/{informe}?limit=500", **admin_auth_headers
        ).status_code == 200

    @pytest.mark.parametrize("valor", ["0", "-5", "muchas"])
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
class TestElCursorEsOpaco:
    def test_un_cursor_corrupto_es_400(self, api_client, admin_auth_headers):
        respuesta = api_client.get(f"{BASE}/flota?cursor=basura", **admin_auth_headers)

        assert respuesta.status_code == 400

    def test_un_cursor_con_componentes_de_menos_es_400(
        self, api_client, admin_auth_headers
    ):
        respuesta = api_client.get(
            f"{BASE}/bajas-unidad?cursor=123", **admin_auth_headers
        )

        assert respuesta.status_code == 400

    def test_un_cursor_vacio_devuelve_la_primera_pagina(
        self, api_client, admin_auth_headers
    ):
        assert api_client.get(
            f"{BASE}/flota?cursor=", **admin_auth_headers
        ).status_code == 200
