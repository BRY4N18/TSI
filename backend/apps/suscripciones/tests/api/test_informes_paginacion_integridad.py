"""T041 — recorrer un listado por páginas devuelve cada fila una sola vez (SC-007).

Incluye `facturas`, cuyo cursor **desempata por texto** (`id_factura` es
`STRING`, no entero). Esa comparación es determinista aunque no ordene
numéricamente, y determinista es lo único que el cursor necesita para no repetir
ni saltar filas — pero conviene comprobarlo, porque es el primer cursor de la
serie que no desempata por un número.
"""

from __future__ import annotations

import json
from urllib.parse import quote

import pytest

BASE = "/api/v1/informes/suscripciones-facturacion"

LISTADOS = ["suscripciones", "facturas", "metodos-pago", "solicitudes-cambio-plan"]


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
        de_una, _ = _recorrer(api_client, admin_auth_headers, informe, limit=1)
        de_dos, _ = _recorrer(api_client, admin_auth_headers, informe, limit=2)

        assert de_una == de_dos

    def test_el_recorrido_termina(
        self, api_client, admin_auth_headers, informe, todo_sembrado
    ):
        filas, paginas = _recorrer(api_client, admin_auth_headers, informe)

        assert paginas == max(len(filas), 1)


@pytest.mark.api
class TestElCursorDeTextoDeFacturas:
    """El primero de la serie que desempata por texto en vez de por un número."""

    def test_recorre_sin_repetir_con_la_misma_fecha_de_emision(
        self, api_client, admin_auth_headers, mock_pinot, facturas_sembradas
    ):
        from conftest import PINOT_STORE
        from apps.suscripciones.tests.conftest import AHORA_MS, CUENTA_A

        # Tres facturas del **mismo instante**: sin el desempate por texto, dos
        # de ellas caerían del mismo lado del cursor y una se perdería.
        for i in ("A", "B", "C"):
            PINOT_STORE["Fact_Factura"].append(
                {
                    "id_factura": f"FAC-202609-0000000{i}", "id_cliente": CUENTA_A,
                    "id_suscripcion": 7001, "idmetodopago": 7601,
                    "numero_factura": f"90{i}", "periodo": "2026-09",
                    "estado_pago": "Pagada", "tipo": "cargo", "es_nota_credito": False,
                    "id_factura_original": None, "motivo_anulacion": None,
                    "activo": True, "reintentos": 0, "monto_base": 10.0,
                    "impuestos": 1.0, "monto_total": 11.0,
                    "fecha_emision": AHORA_MS, "fecha_vencimiento": AHORA_MS,
                    "fecha_actualizacion": AHORA_MS,
                }
            )

        filas, _ = _recorrer(api_client, admin_auth_headers, "facturas")
        numeros = [f["numero_factura"] for f in filas]

        assert len(numeros) == len(set(numeros)), "una factura se repitio entre paginas"
        assert {"90A", "90B", "90C"} <= set(numeros)


@pytest.mark.api
class TestElRecorridoRespetaElAcotamiento:
    def test_paginando_no_se_cuela_la_cuenta_ajena(
        self, api_client, cliente_b_headers, todo_sembrado
    ):
        filas, _ = _recorrer(api_client, cliente_b_headers, "facturas")

        assert {f["cuenta"] for f in filas} == {"Transportes Beltran Ltda."}


@pytest.mark.api
class TestElCursorEsOpaco:
    def test_un_cursor_corrupto_es_400_no_la_primera_pagina(
        self, api_client, admin_auth_headers
    ):
        respuesta = api_client.get(
            f"{BASE}/suscripciones?cursor=basura", **admin_auth_headers
        )

        assert respuesta.status_code == 400

    def test_un_cursor_con_componentes_de_menos_es_400(
        self, api_client, admin_auth_headers
    ):
        respuesta = api_client.get(f"{BASE}/facturas?cursor=123", **admin_auth_headers)

        assert respuesta.status_code == 400

    def test_un_cursor_vacio_devuelve_la_primera_pagina(
        self, api_client, admin_auth_headers
    ):
        respuesta = api_client.get(
            f"{BASE}/suscripciones?cursor=", **admin_auth_headers
        )

        assert respuesta.status_code == 200
