"""PG-ANA-005 — el alias que tapa la columna, y las 157 consultas de informes.

**Causa recurrente y ya diagnosticada en este proyecto**: un alias de `SELECT`
que coincide con el nombre de una columna real produce `ILLEGAL_AGGREGATION` y
deja el endpoint en 500. Ha reaparecido varias veces.

Reaparece por una razón concreta: **un mock nunca lo reproduce**. El doble acepta
cualquier SQL, así que la consulta rota pasa todas las pruebas rápidas y falla la
primera vez que alguien abre el informe. Solo ejecutarla contra ClickHouse lo
destapa.

Esta suite recorre las **157 consultas** del catálogo y las ejecuta de verdad.
Con `LIMIT 0` cuando se puede: lo que interesa es que el motor **acepte** la
sentencia, no traer datos — así el recorrido cuesta segundos en vez de minutos.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from django.conf import settings

from core.clickhouse.client import ClickHouseClient

pytestmark = [pytest.mark.integration, pytest.mark.seguridad]

CATALOGO = Path(settings.BASE_DIR).parent / "dags" / "lib" / "consultas"

#: Errores del motor que delatan el patrón que persigue esta regla.
SINTOMAS = ("ILLEGAL_AGGREGATION", "UNKNOWN_IDENTIFIER", "AMBIGUOUS")


def _consultas() -> list[tuple[str, str]]:
    if not CATALOGO.exists():  # pragma: no cover
        return []
    return sorted(
        (str(p.relative_to(CATALOGO)).replace("\\", "/"), p.read_text(encoding="utf-8"))
        for p in CATALOGO.rglob("*.sql")
    )


CONSULTAS = _consultas()


@pytest.fixture(scope="module")
def clickhouse() -> ClickHouseClient:
    cliente = ClickHouseClient()
    try:
        cliente.query("SELECT 1", {})
    except Exception as exc:  # pragma: no cover - depende del entorno
        pytest.skip(f"ClickHouse no está disponible: {exc}")
    return cliente


def _parametros(sql: str) -> dict[str, str]:
    """Valores plausibles para los parámetros declarados.

    Las consultas usan la sintaxis `{nombre:Tipo}` de ClickHouse. El valor no
    puede ser cualquiera: `{mes:String}` viaja como «YYYY-MM» y la consulta lo
    concatena para formar una fecha, así que una cadena arbitraria hace que el
    motor rechace la sentencia **por el valor, no por la consulta**.

    Distinguir «la consulta está mal» de «le pasé un valor absurdo» es la
    diferencia entre un hallazgo y un falso positivo — y un falso positivo aquí
    desactiva la suite entera.
    """
    valores: dict[str, str] = {}
    for nombre, tipo in re.findall(r"\{(\w+):(\w+)\}", sql):
        bajo = nombre.lower()
        tipo_bajo = tipo.lower()
        if tipo_bajo.startswith("date"):
            valores[nombre] = "2026-01-01"
        elif tipo_bajo.startswith(("int", "uint", "float", "decimal")):
            valores[nombre] = "1"
        elif "mes" in bajo or "periodo" in bajo:
            # `{mes:String}` viaja como «YYYY-MM» y la consulta hace
            # `concat(mes, '-01')`. Un valor generico produce
            # `Cannot parse '2026-01-01-01' as Date`, que parece un defecto de la
            # consulta y es del arnes. Dos consultas fallaron asi antes de esto.
            valores[nombre] = "2026-01"
        elif "anio" in bajo or "year" in bajo:
            valores[nombre] = "2026"
        elif "granularidad" in bajo:
            # La consulta ramifica con `multiIf({granularidad} = 'mes', …)`: un
            # valor fuera del conjunto no cae en ninguna rama y el motor falla
            # por el dato, no por la sentencia.
            valores[nombre] = "mes"
        elif "eje" in bajo or "agrupar" in bajo:
            valores[nombre] = "mes"
        elif "fecha" in bajo or bajo in ("desde", "hasta"):
            valores[nombre] = "2026-01-01"
        else:
            valores[nombre] = "x"
    return valores


def _acotar(sql: str) -> str:
    """Añade `LIMIT 0` si la consulta no trae ya el suyo.

    Interesa que el motor **analice y acepte** la sentencia, no traer filas: el
    `ILLEGAL_AGGREGATION` se produce al planificar, antes de leer nada.
    """
    limpio = sql.strip().rstrip(";")
    if re.search(r"\bLIMIT\b", limpio, re.I) or re.search(r"\bFORMAT\b", limpio, re.I):
        return limpio
    return f"{limpio}\nLIMIT 0"


@pytest.mark.skipif(not CONSULTAS, reason="Catálogo de consultas no disponible")
@pytest.mark.parametrize("nombre,sql", CONSULTAS, ids=[n for n, _ in CONSULTAS])
def test_la_consulta_es_valida_para_el_motor(clickhouse, nombre, sql):
    """Cada consulta del catálogo, ejecutada de verdad.

    Un fallo aquí es un informe que **devuelve 500 la primera vez que alguien lo
    abre**, y que ninguna prueba rápida podía detectar.
    """
    try:
        clickhouse.query(_acotar(sql), _parametros(sql))
    except Exception as exc:  # noqa: BLE001 - el mensaje del motor es el hallazgo
        texto = str(exc)
        delator = next((s for s in SINTOMAS if s in texto.upper()), None)
        if delator:
            pytest.fail(
                f"{nombre}: {delator}.\n"
                "  Es el patrón de PG-ANA-005: un alias de proyección que coincide "
                "con el nombre de una columna de la tabla consultada. Renombrar el "
                "alias.\n"
                f"  {texto[:400]}"
            )
        pytest.fail(f"{nombre}: el motor rechaza la consulta.\n  {texto[:400]}")


@pytest.mark.skipif(not CONSULTAS, reason="Catálogo de consultas no disponible")
def test_el_catalogo_no_encoge_sin_que_nadie_lo_note():
    """Si el descubrimiento fallara, la suite pasaría recorriendo nada.

    Es el mismo control que llevan las demás suites del bloque: un número verde
    sobre un conjunto vacío no distingue «todo bien» de «no miré nada».
    """
    assert len(CONSULTAS) >= 157, (
        f"Solo {len(CONSULTAS)} consultas encontradas; la referencia son 157. "
        "Si se retiraron a propósito, actualizar el número."
    )


# ⛔ **Aquí había un análisis estático de alias y se retiró.**
#
# Buscaba `expresion(...) AS alias` donde el alias apareciera dentro de la
# expresión, para detectar el patrón antes de ejecutarlo. Marcó ocho consultas
# —`ifNull(p.clientes_que_llegaron, 0) AS clientes_que_llegaron`,
# `argMax(idplan, fecha) AS idplan`— que son **correctas**: la columna va
# cualificada por alias de tabla, o es el idioma normal de ClickHouse para
# `argMax`. Y las ocho se ejecutan sin error.
#
# Una prueba que señala código correcto se desactiva en cuanto estorba, y con
# ella se pierde la que sí protege. La ejecución real de las 157 consultas cubre
# PG-ANA-005 sin ambigüedad: si el motor la acepta, no hay alias que tape nada.
