"""T034 — la primera página de los dos listados responde en menos de 2 s (SC-007).

Sobre el Pinot falso el tiempo de red no existe: lo que esta prueba vigila de
verdad es el **número de consultas**, que sí se traslada al stack real. Un `N+1`
—una consulta por fila para resolver un catálogo— pasa desapercibido con seis
filas sembradas y hunde la página con quinientas.
"""

from __future__ import annotations

import time

import pytest
from unittest.mock import patch

BASE = "/api/v1/informes/soporte-cliente"
LISTADOS = ["tickets", "escalados"]

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("informe", LISTADOS)
def test_la_primera_pagina_responde_por_debajo_de_dos_segundos(
    client, agente_informes_headers, informe, todo_sembrado
):
    inicio = time.perf_counter()
    respuesta = client.get(f"{BASE}/{informe}", **agente_informes_headers)
    transcurrido = time.perf_counter() - inicio

    assert respuesta.status_code == 200
    assert transcurrido < 2.0, f"'{informe}' tardo {transcurrido:.2f} s"


@pytest.mark.parametrize("informe", LISTADOS)
def test_el_coste_en_consultas_no_crece_con_el_tamano_de_la_pagina(
    client, agente_informes_headers, informe, todo_sembrado, monkeypatch
):
    """Los catálogos se resuelven **por lote**, no por fila."""
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
        client.get(f"{BASE}/{informe}?limit=1", **agente_informes_headers)
        pocas = len(consultas)

        consultas.clear()
        client.get(f"{BASE}/{informe}?limit=500", **agente_informes_headers)
        muchas = len(consultas)

        # Sin esto, un conteo de cero contra cero pasaria sin ejercitar nada.
        assert pocas > 0, "no se conto ninguna consulta: el contador no esta activo"

        assert muchas == pocas, (
            f"'{informe}' paso de {pocas} a {muchas} consultas al ampliar la pagina: "
            f"algun catalogo se resuelve por fila"
        )
