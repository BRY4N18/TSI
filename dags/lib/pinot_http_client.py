"""Cliente HTTP mínimo a Pinot para los DAGs de informes tácticos compuestos.

Autocontenido a propósito (ver plan.md, Structure Decision / research.md §2):
el contenedor `tactico-airflow-scheduler` no tiene montado `backend/`, así que
no se puede reutilizar `core.pinot.client.PinotClient` (depende de Django).
Mismo comportamiento de fondo: LIMIT explícito por defecto, solo lectura.
"""

from __future__ import annotations

import os
import re
import time
from collections.abc import Callable
from typing import Any

import requests

PINOT_BROKER_URL = os.environ.get("PINOT_BROKER_URL", "http://pinot-broker:8099")
DEFAULT_QUERY_LIMIT = 10_000
#: Timeout de la consulta **dentro de Pinot**, distinto del de `requests`.
#:
#: Sin esta opcion el broker aplica su valor por defecto de 10 s y devuelve
#: `errorCode 427: 1 servers [pinot-server_R] not responded`, que se lee como
#: un servidor caido cuando en realidad solo tardo de mas: el servidor esta
#: sano y la misma consulta responde en 13,5 s si se le da margen. Con
#: `Fact_Accidente` en 2 000 013 filas cualquier extract de varios cientos de
#: miles cruza los 10 s, asi que el valor por defecto ya no da.
QUERY_TIMEOUT_MS = int(os.environ.get("PINOT_QUERY_TIMEOUT_MS", 300_000))
#: El de `requests` va por encima del de Pinot: si se cortase antes, el fallo
#: llegaria como un timeout de red y no como la excepcion que Pinot explica.
HTTP_TIMEOUT_S = QUERY_TIMEOUT_MS / 1000 + 30
#: Reconoce las dos formas: `LIMIT n` y la paginada `LIMIT desplazamiento, n`.
#:
#: La segunda no es un detalle de estilo: sin ella `_with_explicit_limit` no ve
#: ningun limite y anade el suyo, dejando `LIMIT 0, 250000 LIMIT 10000`, que
#: Pinot rechaza al parsear.
_LIMIT_RE = re.compile(r"\blimit\b\s+\d+\s*(?:,\s*\d+\s*)?$", re.IGNORECASE)
_NON_FINITE_TOKENS = {"Infinity", "-Infinity", "NaN"}
_INT_NULL_SENTINEL = -2147483648
_LONG_NULL_SENTINEL = -9223372036854775808


def _quote_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, tuple, set)):
        return "(" + ", ".join(_quote_literal(v) for v in value) + ")"
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def _coerce_value(value: Any, data_type: str) -> Any:
    if value is None:
        return None
    if isinstance(value, str) and value in _NON_FINITE_TOKENS:
        return None
    if data_type == "STRING":
        return None if value == "null" else value
    if data_type in ("INT", "LONG"):
        ivalue = int(value)
        if ivalue in (_INT_NULL_SENTINEL, _LONG_NULL_SENTINEL):
            return None
        return ivalue
    if data_type in ("FLOAT", "DOUBLE"):
        return float(value)
    if data_type == "BOOLEAN":
        return value if isinstance(value, bool) else str(value).lower() == "true"
    return value


def _with_explicit_limit(sql: str) -> str:
    stripped = sql.strip().rstrip(";").rstrip()
    if _LIMIT_RE.search(stripped):
        return stripped
    return f"{stripped} LIMIT {DEFAULT_QUERY_LIMIT}"


#: Codigos con los que el broker responde cuando el servidor no esta disponible:
#: 425 es «no pude conectar con el», 427 «no me contesto».
_CODIGOS_SERVIDOR_AUSENTE = {425, 427}
#: Un `pinot-server` recien arrancado tarda en aceptar consultas, y hasta
#: entonces el broker devuelve 425/427 -indistinguible de un servidor caido-.
#: Sin esta espera, cualquier reinicio de Pinot tumba la tarea que estuviera
#: leyendo aunque el servidor se recupere segundos despues.
REINTENTOS_SERVIDOR = 5
ESPERA_REINTENTO_S = 30


def _servidor_ausente(exceptions: list[dict[str, Any]]) -> bool:
    return any(e.get("errorCode") in _CODIGOS_SERVIDOR_AUSENTE for e in exceptions)


def query_pinot(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Ejecuta una consulta SQL de solo lectura contra el broker de Pinot."""
    rendered_sql = sql % {k: _quote_literal(v) for k, v in (params or {}).items()}
    rendered_sql = _with_explicit_limit(rendered_sql)

    for intento in range(REINTENTOS_SERVIDOR):
        response = requests.post(
            f"{PINOT_BROKER_URL}/query/sql",
            json={
                "sql": rendered_sql,
                "queryOptions": f"timeoutMs={QUERY_TIMEOUT_MS}",
            },
            timeout=HTTP_TIMEOUT_S,
        )
        response.raise_for_status()
        body = response.json()

        exceptions = body.get("exceptions") or []
        if not exceptions or not _servidor_ausente(exceptions):
            break
        if intento < REINTENTOS_SERVIDOR - 1:
            time.sleep(ESPERA_REINTENTO_S)

    if exceptions:
        raise RuntimeError(f"Pinot query failed: {exceptions}")

    result_table = body.get("resultTable")
    if not result_table:
        return []

    columns = result_table["dataSchema"]["columnNames"]
    types = result_table["dataSchema"]["columnDataTypes"]
    rows = result_table["rows"]
    return [
        {col: _coerce_value(val, typ) for col, val, typ in zip(columns, row, types)}
        for row in rows
    ]


#: Cuantas filas se piden por vuelta al leer una tabla grande.
#:
#: 250 000 filas de `Fact_Accidente` son ~15 MB de JSON y se responden en unos
#: pocos segundos. El tamano importa por los dos lados: paginas mas pequenas
#: multiplican las vueltas -y cada una reordena la tabla entera-, y paginas mas
#: grandes devuelven el pico de memoria que la paginacion venia a evitar.
#: Medido contra `Fact_Accidente` con sus 2 000 013 filas, mirando el contador
#: de reinicios del contenedor antes y despues de cada consulta:
#:
#:     10 000 ->  2,2s    50 000 ->  3,7s    250 000 -> 12,5s y el servidor cayo
#:     25 000 ->  2,0s   100 000 ->  5,9s
#:
#: 50 000 deja margen sobre el ultimo tamano que se comporto de forma estable.
#: Subirlo apenas ahorra tiempo -la lectura completa no es el cuello- y acerca
#: otra vez al punto donde el servidor se cae en mitad de la carga.
TAMANO_PAGINA = 50_000


def query_pinot_paginado(
    sql: str,
    clave_orden: str,
    limite_total: int,
    params: dict[str, Any] | None = None,
    tamano_pagina: int = TAMANO_PAGINA,
    consultar: Callable[[str, dict[str, Any] | None], list[dict[str, Any]]] = query_pinot,
) -> list[dict[str, Any]]:
    """Lee una tabla grande por trozos en vez de en una sola respuesta.

    `Fact_Accidente` paso de miles de filas a 2 000 013 con la carga del CSV, y
    una sola lectura de ese tamano no es viable: son ~116 MB de JSON que hay que
    materializar enteros antes de poder tocarlos.

    ⚠️ **El `ORDER BY` no es cosmetico: sin el, la paginacion se corrompe.**
    Pinot no garantiza ningun orden entre consultas, asi que dos paginas
    consecutivas pueden repetir filas y saltarse otras. Y no fallaria: el hecho
    saldria con el numero de filas esperado y con casos duplicados y ausentes
    mezclados, que es justo lo que nadie revisa. `clave_orden` debe ser unica.

    ⚠️ **Se avanza por clave (`WHERE clave > ultima`), no por desplazamiento.**
    `LIMIT <desplazamiento>, <n>` parece lo natural y tumba el servidor: Pinot
    ordena la tabla entera en cada pagina y materializa `desplazamiento + n`
    filas, asi que la ultima pagina de 2 000 013 cuesta como leerlas todas. Con
    2 GB de heap eso mata al `pinot-server`, y el fallo llega disfrazado -el
    broker responde `Connection refused` y parece un problema de red-. Avanzar
    por clave deja cada pagina con el mismo coste, la primera y la ultima.
    """
    filas: list[dict[str, Any]] = []
    base = sql.strip().rstrip(";").rstrip()
    base = _LIMIT_RE.sub("", base).rstrip()
    # el filtro se encadena a la condicion existente si la consulta ya trae una
    conector = "AND" if re.search(r"\bwhere\b", base, re.IGNORECASE) else "WHERE"
    ultima: Any = None

    while len(filas) < limite_total:
        pagina = min(tamano_pagina, limite_total - len(filas))
        avance = "" if ultima is None else f" {conector} {clave_orden} > {_quote_literal(ultima)}"
        trozo = consultar(
            f"{base}{avance} ORDER BY {clave_orden} LIMIT {pagina}", params
        )
        if not trozo:
            break
        filas.extend(trozo)
        ultima = trozo[-1][clave_orden]
        # una pagina corta significa que la tabla se acabo; pedir la siguiente
        # solo devolveria vacio.
        if len(trozo) < pagina:
            break
    return filas
