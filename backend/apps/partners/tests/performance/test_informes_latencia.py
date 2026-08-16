"""T041 — la primera página de los cinco listados responde en menos de 2 s (SC-007).

Sobre el Pinot falso, el tiempo de red no existe: lo que esta prueba vigila es
el **número de consultas**, que sí se traslada al stack real. Un `N+1` —una
consulta por fila para resolver un catálogo— pasa desapercibido con seis filas
sembradas y hunde la página con quinientas.
"""

from __future__ import annotations

import time

import pytest

BASE = "/api/v1/informes/partners-api"
LISTADOS = [
    "partners",
    "credenciales",
    "cambios-acceso",
    "versiones-contrato",
    "alcance-datos",
]

#: Cuántas consultas de catálogo pueden aparecer solo cuando la página trae
#: filas de cierta forma. Es un coste **por página**, no por fila.
COTA_CATALOGOS_CONDICIONALES = 2

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("informe", LISTADOS)
def test_la_primera_pagina_responde_por_debajo_de_dos_segundos(
    client, gestor_headers, informe, todo_sembrado
):
    inicio = time.perf_counter()
    respuesta = client.get(f"{BASE}/{informe}", **gestor_headers)
    transcurrido = time.perf_counter() - inicio

    assert respuesta.status_code == 200
    assert transcurrido < 2.0, f"'{informe}' tardó {transcurrido:.2f} s"


@pytest.mark.parametrize("informe", LISTADOS)
def test_el_coste_en_consultas_no_crece_con_el_tamano_de_la_pagina(
    client, gestor_headers, informe, todo_sembrado, monkeypatch
):
    """Los catálogos se resuelven **por lote**, no por fila.

    Es la diferencia entre un coste fijo por petición y uno proporcional al
    número de filas — que es lo que convierte una página de quinientas en una
    espera de minutos contra el Pinot real.
    """
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

    monkeypatch.setattr(PinotClient, "query", contando)

    consultas.clear()
    client.get(f"{BASE}/{informe}?limit=1", **gestor_headers)
    pocas = len(consultas)

    consultas.clear()
    client.get(f"{BASE}/{informe}?limit=500", **gestor_headers)
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