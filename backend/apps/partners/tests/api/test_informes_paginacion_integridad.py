"""T039 y T040 — integridad del recorrido y `limit` que no se recorta.

El recorrido se prueba **sin filtro de estado**. Con `estado` puesto, L1 refina
en Python lo que no puede empujar a SQL y una página puede devolver menos filas
que `limit` — comportamiento declarado, no defecto, pero que haría de esta
prueba una comprobación de otra cosa.
"""

from __future__ import annotations

import json
from urllib.parse import quote

import pytest

BASE = "/api/v1/informes/partners-api"

#: Los tres de acceso; los dos de gestión se recorren con el mismo gestor.
LISTADOS = [
    "partners",
    "credenciales",
    "cambios-acceso",
    "versiones-contrato",
    "alcance-datos",
]

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
    raise AssertionError(f"'{informe}' no terminó de paginar en {tope} páginas")


@pytest.mark.parametrize("informe", LISTADOS)
class TestIntegridadDelRecorrido:
    def test_coincide_con_la_lectura_de_una_pagina(
        self, client, gestor_headers, informe, todo_sembrado
    ):
        de_una_vez = client.get(
            f"{BASE}/{informe}?limit=500", **gestor_headers
        ).json()["data"]

        por_paginas, _ = _recorrer(client, gestor_headers, informe)

        assert por_paginas == de_una_vez

    def test_ninguna_fila_se_repite(
        self, client, gestor_headers, informe, todo_sembrado
    ):
        filas, _ = _recorrer(client, gestor_headers, informe)
        serializadas = [json.dumps(f, sort_keys=True) for f in filas]

        assert len(serializadas) == len(set(serializadas))

    def test_el_tamano_de_pagina_no_altera_el_contenido(
        self, client, gestor_headers, informe, todo_sembrado
    ):
        de_una, _ = _recorrer(client, gestor_headers, informe, limit=1)
        de_dos, _ = _recorrer(client, gestor_headers, informe, limit=2)

        assert de_una == de_dos


class TestElRecorridoRespetaElAcotamiento:
    def test_paginando_no_se_cuela_un_partner_ajeno(
        self, client, partner_a_informes_headers, todo_sembrado
    ):
        filas, _ = _recorrer(client, partner_a_informes_headers, "partners")

        assert "Andina Conecta" not in {f["nombre_partner"] for f in filas}


@pytest.mark.parametrize("informe", LISTADOS)
class TestLimite:
    """Sobre el máximo es `400`: recortar en silencio daría por completa una
    lectura que no lo está."""

    def test_sobre_el_maximo_es_400(self, client, gestor_headers, informe):
        assert client.get(
            f"{BASE}/{informe}?limit=5000", **gestor_headers
        ).status_code == 400

    def test_el_error_nombra_el_maximo(self, client, gestor_headers, informe):
        cuerpo = client.get(f"{BASE}/{informe}?limit=5000", **gestor_headers).json()

        assert "500" in cuerpo["detail"]

    def test_no_devuelve_datos_recortados(self, client, gestor_headers, informe):
        cuerpo = client.get(f"{BASE}/{informe}?limit=5000", **gestor_headers).json()

        assert "data" not in cuerpo

    def test_el_maximo_exacto_se_admite(self, client, gestor_headers, informe):
        assert client.get(
            f"{BASE}/{informe}?limit=500", **gestor_headers
        ).status_code == 200

    @pytest.mark.parametrize("valor", ["0", "-5", "muchas"])
    def test_valores_invalidos_son_400(self, client, gestor_headers, informe, valor):
        assert client.get(
            f"{BASE}/{informe}?limit={valor}", **gestor_headers
        ).status_code == 400

    def test_por_defecto_es_50(self, client, gestor_headers, informe):
        cuerpo = client.get(f"{BASE}/{informe}", **gestor_headers).json()

        assert cuerpo["meta"]["pagination"]["limit"] == 50

    def test_un_dir_invalido_es_400(self, client, gestor_headers, informe):
        assert client.get(
            f"{BASE}/{informe}?dir=arriba", **gestor_headers
        ).status_code == 400

    def test_vacio_es_200_nunca_404(self, client, gestor_headers, informe):
        assert client.get(f"{BASE}/{informe}", **gestor_headers).status_code == 200


class TestElCursorEsOpaco:
    def test_un_cursor_corrupto_es_400(self, client, gestor_headers):
        assert client.get(
            f"{BASE}/partners?cursor=basura", **gestor_headers
        ).status_code == 400

    def test_un_cursor_con_componentes_de_menos_es_400(self, client, gestor_headers):
        assert client.get(
            f"{BASE}/cambios-acceso?cursor=123", **gestor_headers
        ).status_code == 400

    def test_un_cursor_vacio_devuelve_la_primera_pagina(self, client, gestor_headers):
        assert client.get(
            f"{BASE}/partners?cursor=", **gestor_headers
        ).status_code == 200
