"""T025/T034 — latencia y, sobre todo, coste en consultas.

Sobre el Pinot falso el tiempo de red no existe. Lo que estas pruebas vigilan de
verdad es el **número de consultas**, que sí se traslada al stack real.

Aquí importa más que en ningún módulo anterior: el acotamiento por zona es
precisamente el patrón que la spec descartó resolver fila a fila. Si el coste
creciera con el número de zonas contratadas o con el tamaño de la página,
volvería a ser trabajo proporcional en vez de un filtro.
"""

from __future__ import annotations

import time

import pytest
from unittest.mock import patch

BASE = "/api/v1/informes/emergencias"
LISTADOS = ["casos", "despachos", "evidencia-fotos", "notas-campo", "cierres"]

#: Cuántas consultas de catálogo pueden aparecer solo cuando la página trae
#: filas de cierta forma. Es un coste **por página**, no por fila.
COTA_CATALOGOS_CONDICIONALES = 2

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("informe", LISTADOS)
def test_la_primera_pagina_responde_por_debajo_de_dos_segundos(
    client, operador_informes_headers, informe, emergencias_sembradas
):
    inicio = time.perf_counter()
    respuesta = client.get(f"{BASE}/{informe}", **operador_informes_headers)
    transcurrido = time.perf_counter() - inicio

    assert respuesta.status_code == 200
    assert transcurrido < 2.0, f"'{informe}' tardo {transcurrido:.2f} s"


def test_la_primera_pagina_de_un_cliente_acotado_tambien(
    client, cliente_informes_headers, emergencias_sembradas
):
    """Con el acotamiento por zona resuelto, que es el camino mas largo."""
    inicio = time.perf_counter()
    respuesta = client.get(f"{BASE}/casos", **cliente_informes_headers)
    transcurrido = time.perf_counter() - inicio

    assert respuesta.status_code == 200
    assert transcurrido < 2.0


@pytest.mark.parametrize("informe", LISTADOS)
def test_el_coste_en_consultas_no_crece_con_el_tamano_de_la_pagina(
    client, operador_informes_headers, informe, emergencias_sembradas, monkeypatch
):
    """Los catalogos se resuelven **por lote**, no por fila."""
    from core.pinot.client import PinotClient

    consultas: list[int] = []
    original = PinotClient.query

    def contando(self, sql, params=None):
        consultas.append(1)
        # ⚠️ `original` es el mock que instala `mock_pinot`, y ese mock se llama
        # **sin** `self`. Pasárselo lo hace fallar con `TypeError`, la petición
        # acaba en `401` y el conteo queda en cero — con lo que la comprobación
        # `muchas == pocas` pasaría comparando nada contra nada.
        return original(sql, params)

    # ⚠️ **Contexto, no `monkeypatch`** — y la diferencia no es de estilo.
    # `original` es el mock que instala `mock_pinot` mediante `patch.object`.
    # `monkeypatch` guardaba **ese mock** como valor previo y lo reinstalaba al
    # deshacerse; si su teardown corría **después** del de `mock_pinot` —el
    # orden depende de por qué fixture llega cada uno—, `PinotClient.query`
    # quedaba con el mock puesto **para el resto de la sesión**. Las cinco
    # pruebas de `test_pinot_client_limit` fallaban por eso, y solo cuando se
    # ejecutaban junto a esta app.
    #
    # Un `with` sale siempre al terminar el cuerpo, antes que cualquier fixture.
    with patch.object(PinotClient, "query", contando):

        consultas.clear()
        client.get(f"{BASE}/{informe}?limit=1", **operador_informes_headers)
        pocas = len(consultas)

        consultas.clear()
        client.get(f"{BASE}/{informe}?limit=500", **operador_informes_headers)
        muchas = len(consultas)

        # Sin esto, un conteo de cero contra cero pasaria sin ejercitar nada.
        assert pocas > 0, "no se conto ninguna consulta: el contador no esta activo"

        # ⚠️ Lo que importa es que el coste sea **constante en filas**, no que sea
        # idéntico: un catálogo que solo aplica a algunas filas —la credencial de un
        # evento, el condado de un caso— cuesta **una** consulta más para toda la
        # página, no una por fila. Exigir igualdad exacta haría fallar la prueba por
        # un comportamiento correcto; la cota fija es la que detecta el `N+1` real.
        assert muchas <= pocas + COTA_CATALOGOS_CONDICIONALES, (
            f"'{informe}' pasó de {pocas} a {muchas} consultas al ampliar la página: "
            f"algún catálogo se resuelve por fila"
        )

def test_el_coste_del_acotamiento_no_crece_con_el_numero_de_zonas(
    client, cliente_informes_headers, emergencias_sembradas, monkeypatch
):
    """La comprobacion que hace de este eje un filtro y no un recorrido.

    Con la resolucion fila a fila que el modulo operativo usa hoy, el coste
    creceria con las zonas **y** con las filas recorridas.
    """
    from conftest import PINOT_STORE
    from core.pinot.client import PinotClient
    from apps.accidentes.tests.informes_fixtures import (
        CONDADO_AJENO,
        CONDADO_CONTRATADO,
        CUENTA_CLIENTE,
    )

    consultas: list[int] = []
    original = PinotClient.query

    def contando(self, sql, params=None):
        consultas.append(1)
        # ⚠️ `original` es el mock que instala `mock_pinot`, y ese mock se llama
        # **sin** `self`. Pasárselo lo hace fallar con `TypeError`, la petición
        # acaba en `401` y el conteo queda en cero — con lo que la comprobación
        # `muchas == pocas` pasaría comparando nada contra nada.
        return original(sql, params)

    # ⚠️ **Contexto, no `monkeypatch`** — y la diferencia no es de estilo.
    # `original` es el mock que instala `mock_pinot` mediante `patch.object`.
    # `monkeypatch` guardaba **ese mock** como valor previo y lo reinstalaba al
    # deshacerse; si su teardown corría **después** del de `mock_pinot` —el
    # orden depende de por qué fixture llega cada uno—, `PinotClient.query`
    # quedaba con el mock puesto **para el resto de la sesión**. Las cinco
    # pruebas de `test_pinot_client_limit` fallaban por eso, y solo cuando se
    # ejecutaban junto a esta app.
    #
    # Un `with` sale siempre al terminar el cuerpo, antes que cualquier fixture.
    with patch.object(PinotClient, "query", contando):

        consultas.clear()
        client.get(f"{BASE}/casos?limit=500", **cliente_informes_headers)
        con_una_zona = len(consultas)

        for fila in PINOT_STORE["Dim_Preferencias_Cliente"]:
            if fila.get("id_cliente") == CUENTA_CLIENTE:
                fila["zonas_geograficas"] = f"[{CONDADO_CONTRATADO},{CONDADO_AJENO}]"

        consultas.clear()
        respuesta = client.get(f"{BASE}/casos?limit=500", **cliente_informes_headers)
        con_dos_zonas = len(consultas)

        assert respuesta.status_code == 200
        assert con_dos_zonas == con_una_zona
