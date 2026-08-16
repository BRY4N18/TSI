"""T041 — recorrer un listado por páginas devuelve cada fila exactamente una vez (SC-006).

**`demos-activas` queda excluido a propósito**, y no por comodidad: su recorrido
admite páginas cortas por diseño (research D3), así que comparar «de una vez»
contra «por páginas» exigiría replicar aquí la lógica del refinamiento. Su
integridad se verifica en `test_informes_demos_pagina_corta.py`, que sí conoce
esa particularidad.
"""

from __future__ import annotations

import json
from urllib.parse import quote

import pytest

BASE = "/api/v1/informes/ventas-crm"

LISTADOS = ["prospectos", "reasignaciones", "notificaciones-enviadas"]


@pytest.fixture
def todo_sembrado(dos_carteras, asignaciones_sembradas, notificaciones_sembradas):
    return True


def _recorrer(api_client, headers, informe, limit=1, tope=100):
    filas = []
    cursor = None
    paginas = 0
    while paginas < tope:
        url = f"{BASE}/{informe}?limit={limit}"
        if cursor:
            # El cursor es opaco: se reenvía tal cual, sin interpretarlo.
            url += f"&cursor={quote(cursor)}"
        cuerpo = api_client.get(url, **headers).json()
        filas.extend(cuerpo["data"])
        paginas += 1
        cursor = cuerpo["meta"]["pagination"]["cursor"]
        if cursor is None:
            return filas, paginas
    raise AssertionError(f"'{informe}' no termino de paginar en {tope} paginas")


@pytest.mark.api
@pytest.mark.parametrize("informe", LISTADOS)
class TestIntegridadDelRecorrido:
    def test_coincide_con_la_lectura_de_una_pagina(
        self, api_client, admin_auth_headers, informe, todo_sembrado
    ):
        de_una_vez = api_client.get(
            f"{BASE}/{informe}?limit=500", **admin_auth_headers
        ).json()["data"]

        por_paginas, _ = _recorrer(api_client, admin_auth_headers, informe)

        assert por_paginas == de_una_vez, (
            "el recorrido por paginas no reproduce la lectura completa: "
            "hay filas repetidas, saltadas o en distinto orden"
        )

    def test_ninguna_fila_se_repite(
        self, api_client, admin_auth_headers, informe, todo_sembrado
    ):
        filas, _ = _recorrer(api_client, admin_auth_headers, informe)

        serializadas = [json.dumps(f, sort_keys=True) for f in filas]
        assert len(serializadas) == len(set(serializadas))

    def test_el_tamano_de_pagina_no_altera_el_contenido(
        self, api_client, admin_auth_headers, informe, todo_sembrado
    ):
        # Si lo altera, el desempate del cursor está mal y el fallo depende de
        # dónde caiga el corte de página.
        de_una, _ = _recorrer(api_client, admin_auth_headers, informe, limit=1)
        de_dos, _ = _recorrer(api_client, admin_auth_headers, informe, limit=2)

        assert de_una == de_dos

    def test_el_recorrido_termina(
        self, api_client, admin_auth_headers, informe, todo_sembrado
    ):
        filas, paginas = _recorrer(api_client, admin_auth_headers, informe)

        assert paginas == max(len(filas), 1)


@pytest.mark.api
class TestElRecorridoRespetaElAcotamiento:
    def test_paginando_no_se_cuela_cartera_ajena(
        self, api_client, gerente_b_headers, dos_carteras
    ):
        """El acotamiento no puede perderse entre páginas."""
        filas, _ = _recorrer(api_client, gerente_b_headers, "prospectos")

        assert {f["empresa"] for f in filas} == {"Delta Transportes", "Epsilon Flotas"}


@pytest.mark.api
class TestElCursorEsOpaco:
    def test_un_cursor_corrupto_es_400_no_la_primera_pagina(
        self, api_client, admin_auth_headers
    ):
        respuesta = api_client.get(f"{BASE}/prospectos?cursor=basura", **admin_auth_headers)

        assert respuesta.status_code == 400

    def test_un_cursor_con_componentes_de_menos_es_400(
        self, api_client, admin_auth_headers
    ):
        respuesta = api_client.get(
            f"{BASE}/reasignaciones?cursor=123", **admin_auth_headers
        )

        assert respuesta.status_code == 400

    def test_un_cursor_vacio_devuelve_la_primera_pagina(
        self, api_client, admin_auth_headers
    ):
        respuesta = api_client.get(f"{BASE}/prospectos?cursor=", **admin_auth_headers)

        assert respuesta.status_code == 200
