"""T032/T033 equivalentes — integridad del recorrido y `limit` en los cinco.

Los cinco listados se recorren desde aquí aunque uno viva en `seguimiento`: el
recorrido es una propiedad del departamento, no de la app que sirve la ruta, y
partirlo en dos ficheros haría fácil que uno de los dos se quedara sin cubrir.
"""

from __future__ import annotations

import json
from urllib.parse import quote

import pytest

BASE = "/api/v1/informes/emergencias"
LISTADOS = ["casos", "despachos", "evidencia-fotos", "notas-campo", "cierres"]

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
        self, client, operador_informes_headers, informe, emergencias_sembradas
    ):
        de_una_vez = client.get(
            f"{BASE}/{informe}?limit=500", **operador_informes_headers
        ).json()["data"]

        por_paginas, _ = _recorrer(client, operador_informes_headers, informe)

        assert por_paginas == de_una_vez

    def test_ninguna_fila_se_repite(
        self, client, operador_informes_headers, informe, emergencias_sembradas
    ):
        filas, _ = _recorrer(client, operador_informes_headers, informe)
        serializadas = [json.dumps(f, sort_keys=True) for f in filas]

        assert len(serializadas) == len(set(serializadas))

    def test_el_tamano_de_pagina_no_altera_el_contenido(
        self, client, operador_informes_headers, informe, emergencias_sembradas
    ):
        de_una, _ = _recorrer(client, operador_informes_headers, informe, limit=1)
        de_dos, _ = _recorrer(client, operador_informes_headers, informe, limit=2)

        assert de_una == de_dos

    def test_el_recorrido_termina(
        self, client, operador_informes_headers, informe, emergencias_sembradas
    ):
        filas, paginas = _recorrer(client, operador_informes_headers, informe)

        assert paginas == max(len(filas), 1)


class TestElRecorridoRespetaElAcotamiento:
    def test_paginando_no_se_cuelan_casos_de_zonas_ajenas(
        self, client, cliente_informes_headers, emergencias_sembradas
    ):
        """Recorrer página a página no debe abrir lo que una sola página cierra."""
        filas, _ = _recorrer(client, cliente_informes_headers, "casos")

        assert filas
        assert {f["condado"] for f in filas} == {"Valle Norte"}

    def test_paginando_el_cliente_sigue_sin_ver_casos_abiertos(
        self, client, cliente_informes_headers, emergencias_sembradas
    ):
        filas, _ = _recorrer(client, cliente_informes_headers, "casos")

        assert all(f["activo"] is False for f in filas)


@pytest.mark.parametrize("informe", LISTADOS)
class TestLimite:
    def test_sobre_el_maximo_es_400(
        self, client, operador_informes_headers, informe
    ):
        assert client.get(
            f"{BASE}/{informe}?limit=5000", **operador_informes_headers
        ).status_code == 400

    def test_el_error_nombra_el_maximo(
        self, client, operador_informes_headers, informe
    ):
        cuerpo = client.get(
            f"{BASE}/{informe}?limit=5000", **operador_informes_headers
        ).json()

        assert "500" in cuerpo["detail"]

    def test_no_devuelve_datos_recortados(
        self, client, operador_informes_headers, informe
    ):
        cuerpo = client.get(
            f"{BASE}/{informe}?limit=5000", **operador_informes_headers
        ).json()

        assert "data" not in cuerpo

    def test_el_maximo_exacto_se_admite(
        self, client, operador_informes_headers, informe
    ):
        assert client.get(
            f"{BASE}/{informe}?limit=500", **operador_informes_headers
        ).status_code == 200

    @pytest.mark.parametrize("valor", ["0", "-5", "muchas"])
    def test_valores_invalidos_son_400(
        self, client, operador_informes_headers, informe, valor
    ):
        assert client.get(
            f"{BASE}/{informe}?limit={valor}", **operador_informes_headers
        ).status_code == 400

    def test_por_defecto_es_50(self, client, operador_informes_headers, informe):
        cuerpo = client.get(
            f"{BASE}/{informe}", **operador_informes_headers
        ).json()

        assert cuerpo["meta"]["pagination"]["limit"] == 50

    def test_un_dir_invalido_es_400(
        self, client, operador_informes_headers, informe
    ):
        assert client.get(
            f"{BASE}/{informe}?dir=arriba", **operador_informes_headers
        ).status_code == 400

    def test_vacio_es_200_nunca_404(
        self, client, operador_informes_headers, informe
    ):
        assert client.get(
            f"{BASE}/{informe}", **operador_informes_headers
        ).status_code == 200


class TestElCursorEsOpaco:
    def test_un_cursor_corrupto_es_400(self, client, operador_informes_headers):
        assert client.get(
            f"{BASE}/casos?cursor=basura", **operador_informes_headers
        ).status_code == 400

    def test_un_cursor_con_componentes_de_menos_es_400(
        self, client, operador_informes_headers
    ):
        assert client.get(
            f"{BASE}/despachos?cursor=123", **operador_informes_headers
        ).status_code == 400

    def test_un_cursor_vacio_devuelve_la_primera_pagina(
        self, client, operador_informes_headers
    ):
        assert client.get(
            f"{BASE}/casos?cursor=", **operador_informes_headers
        ).status_code == 200
