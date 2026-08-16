"""T032 y T033 — integridad del recorrido y `limit` que no se recorta."""

from __future__ import annotations

import json
from urllib.parse import quote

import pytest

BASE = "/api/v1/informes/soporte-cliente"
LISTADOS = ["tickets", "escalados"]

pytestmark = pytest.mark.django_db


def _recorrer(client, headers, informe, limit=1, tope=100):
    filas = []
    cursor = None
    paginas = 0
    while paginas < tope:
        url = f"{BASE}/{informe}?limit={limit}"
        if cursor:
            url += f"&cursor={quote(cursor)}"
        cuerpo = client.get(url, **headers).json()
        filas.extend(cuerpo["data"])
        paginas += 1
        cursor = cuerpo["meta"]["pagination"]["cursor"]
        if cursor is None:
            return filas, paginas
    raise AssertionError(f"'{informe}' no termino de paginar en {tope} paginas")


@pytest.mark.parametrize("informe", LISTADOS)
class TestIntegridadDelRecorrido:
    def test_coincide_con_la_lectura_de_una_pagina(
        self, client, agente_informes_headers, informe, todo_sembrado
    ):
        de_una_vez = client.get(
            f"{BASE}/{informe}?limit=500", **agente_informes_headers
        ).json()["data"]

        por_paginas, _ = _recorrer(client, agente_informes_headers, informe)

        assert por_paginas == de_una_vez

    def test_ninguna_fila_se_repite(
        self, client, agente_informes_headers, informe, todo_sembrado
    ):
        filas, _ = _recorrer(client, agente_informes_headers, informe)
        serializadas = [json.dumps(f, sort_keys=True) for f in filas]

        assert len(serializadas) == len(set(serializadas))

    def test_el_tamano_de_pagina_no_altera_el_contenido(
        self, client, agente_informes_headers, informe, todo_sembrado
    ):
        de_una, _ = _recorrer(client, agente_informes_headers, informe, limit=1)
        de_dos, _ = _recorrer(client, agente_informes_headers, informe, limit=2)

        assert de_una == de_dos

    def test_el_recorrido_termina(
        self, client, agente_informes_headers, informe, todo_sembrado
    ):
        filas, paginas = _recorrer(client, agente_informes_headers, informe)

        assert paginas == max(len(filas), 1)


class TestElRecorridoRespetaElAcotamiento:
    def test_paginando_no_se_cuelan_tickets_ajenos(
        self, client, partner_informes_headers, todo_sembrado
    ):
        filas, _ = _recorrer(client, partner_informes_headers, "tickets")

        assert filas
        assert {f["cuenta"] for f in filas} == {"Navarro Integraciones Ltda."}


@pytest.mark.parametrize("informe", LISTADOS)
class TestLimite:
    def test_sobre_el_maximo_es_400(self, client, agente_informes_headers, informe):
        assert client.get(
            f"{BASE}/{informe}?limit=5000", **agente_informes_headers
        ).status_code == 400

    def test_el_error_nombra_el_maximo(self, client, agente_informes_headers, informe):
        cuerpo = client.get(
            f"{BASE}/{informe}?limit=5000", **agente_informes_headers
        ).json()

        assert "500" in cuerpo["detail"]

    def test_no_devuelve_datos_recortados(
        self, client, agente_informes_headers, informe
    ):
        cuerpo = client.get(
            f"{BASE}/{informe}?limit=5000", **agente_informes_headers
        ).json()

        assert "data" not in cuerpo

    def test_el_maximo_exacto_se_admite(
        self, client, agente_informes_headers, informe
    ):
        assert client.get(
            f"{BASE}/{informe}?limit=500", **agente_informes_headers
        ).status_code == 200

    @pytest.mark.parametrize("valor", ["0", "-5", "muchas"])
    def test_valores_invalidos_son_400(
        self, client, agente_informes_headers, informe, valor
    ):
        assert client.get(
            f"{BASE}/{informe}?limit={valor}", **agente_informes_headers
        ).status_code == 400

    def test_por_defecto_es_50(self, client, agente_informes_headers, informe):
        cuerpo = client.get(f"{BASE}/{informe}", **agente_informes_headers).json()

        assert cuerpo["meta"]["pagination"]["limit"] == 50

    def test_un_dir_invalido_es_400(self, client, agente_informes_headers, informe):
        assert client.get(
            f"{BASE}/{informe}?dir=arriba", **agente_informes_headers
        ).status_code == 400


class TestElCursorEsOpaco:
    def test_un_cursor_corrupto_es_400(self, client, agente_informes_headers):
        assert client.get(
            f"{BASE}/tickets?cursor=basura", **agente_informes_headers
        ).status_code == 400

    def test_un_cursor_con_componentes_de_menos_es_400(
        self, client, agente_informes_headers
    ):
        assert client.get(
            f"{BASE}/escalados?cursor=123", **agente_informes_headers
        ).status_code == 400

    def test_un_cursor_vacio_devuelve_la_primera_pagina(
        self, client, agente_informes_headers
    ):
        assert client.get(
            f"{BASE}/tickets?cursor=", **agente_informes_headers
        ).status_code == 200
