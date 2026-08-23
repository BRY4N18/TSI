"""Una base de datos aparte para las pruebas que insertan su propio escenario.

⚠️ **Existe porque seis pruebas dependían de que el modelo estuviera vacío.**

`test_ot06_mrr` insertaba dos suscripciones y exigía un MRR de 220. Pasaba
mientras `hecho_suscripcion` no tenía nada más. El día que se cargaron los
hechos de verdad —siete suscripciones reales— el mismo cálculo dio 667 y la
prueba se cayó **sin que el informe hubiera cambiado**.

Los ayudantes `limpiar_*()` no eran el problema: borran solo sus propias filas,
que es lo correcto para no destruir el modelo cargado. El problema es comparar un
escenario de tres filas contra un total **global**.

Aislar por base resuelve la familia entera de una vez:

* la prueba compara contra un total que **sí** controla, porque no hay nada más;
* el modelo cargado no se toca, así que las pruebas que sí quieren medirlo
  —`TestSobreElModeloCargado`— siguen viendo lo real;
* no hay que acotar cada aserción una a una, que es donde se olvida justo la que
  importa.

⚠️ **No es automática.** Se pide con la fixture `base_propia`: una prueba que
quiera medir el modelo real no debe recibir una base vacía sin enterarse.
"""

from __future__ import annotations

import os

import pytest

#: Nombre de la base aislada. Distinto del de producción **y evidente**: si
#: alguien la ve en un `SHOW DATABASES` tiene que saber qué es sin preguntar.
BASE_PRUEBAS = os.environ.get("CLICKHOUSE_DB_PRUEBAS", "tsi_tactico_pruebas")


def _crear_base() -> None:
    """Crea la base y su esquema. Idempotente."""
    import requests

    from lib import clickhouse_http_client as ch

    # `CREATE DATABASE` no puede ir contra la base que se está creando, así que
    # esta llamada no pasa por `execute_clickhouse` —que fija `database`—.
    respuesta = requests.post(
        ch.CLICKHOUSE_URL,
        data=f"CREATE DATABASE IF NOT EXISTS {BASE_PRUEBAS}".encode("utf-8"),
        auth=(ch.CLICKHOUSE_USER, ch.CLICKHOUSE_PASSWORD),
        timeout=30,
    )
    if respuesta.status_code != 200:
        raise RuntimeError(f"no se pudo crear {BASE_PRUEBAS}: {respuesta.text}")


@pytest.fixture
def base_propia(monkeypatch):
    """Apunta el cliente de ClickHouse a una base vacía, solo para esta prueba.

    Devuelve el nombre de la base, por si la prueba necesita nombrarla.

    ⚠️ Se parchea el **atributo del módulo**, no la variable de entorno: las
    funciones leen `CLICKHOUSE_DB` global en cada llamada, así que el parche
    surte efecto de inmediato y `monkeypatch` lo revierte al terminar. Cambiar el
    entorno no bastaría —el valor ya está leído— y dejaría la sesión apuntando a
    la base de pruebas si algo fallara a mitad.
    """
    from lib import clickhouse_http_client as ch
    from lib import ddl

    _crear_base()
    monkeypatch.setattr(ch, "CLICKHOUSE_DB", BASE_PRUEBAS)
    ddl.ensure_modelo_analitico()

    yield BASE_PRUEBAS


def vaciar(*tablas: str) -> None:
    """Deja las tablas dadas sin una sola fila.

    Solo tiene sentido dentro de `base_propia`: contra el modelo cargado esto
    **borraría datos reales**, y por eso comprueba contra qué base apunta antes
    de tocar nada.
    """
    from lib import clickhouse_http_client as ch

    if ch.CLICKHOUSE_DB != BASE_PRUEBAS:
        raise RuntimeError(
            f"`vaciar()` solo corre sobre {BASE_PRUEBAS}; apunta a "
            f"{ch.CLICKHOUSE_DB}. Falta la fixture `base_propia`."
        )
    for tabla in tablas:
        ch.execute_clickhouse(f"TRUNCATE TABLE IF EXISTS {tabla}")
