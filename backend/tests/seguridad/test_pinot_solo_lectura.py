"""PG-OPE-007 — Pinot es de solo lectura desde Django.

La regla de oro del modelo de datos (`infrastructure.md` §1): el **único** canal
de escritura es Kafka. Django publica un evento, Pinot lo ingiere, y las lecturas
van por SQL directo al broker.

Escribir contra Pinot saltándose Kafka no produce un error visible: la fila entra
o no entra según el upsert, el evento nunca existe, y cualquier consumidor futuro
—un DAG, una reconciliación, otro servicio— no se entera de que ese dato pasó por
el sistema. Es un fallo silencioso que solo aparece cuando alguien compara dos
fuentes y no cuadran.

**Por qué análisis estático y no una prueba de comportamiento.** Un `INSERT`
contra Pinot no falla de forma observable en una suite con mocks —el doble acepta
cualquier SQL, como demostró `PG-SEC-005` (`changelog.md` C8)—. Lo que se puede
comprobar de verdad es que **la sentencia no está escrita en el árbol**.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from django.conf import settings

pytestmark = [pytest.mark.unit, pytest.mark.seguridad]

RAIZ = Path(settings.BASE_DIR)

#: Directorios donde vive la lógica que habla con Pinot.
AMBITO = ("core", "apps")

#: Verbos de escritura **con su sintaxis obligatoria**. Exigir la palabra que los
#: sigue (`INTO`, `FROM`, `TABLE`, `SET`) no es cosmético: sin ella el patrón
#: capturaba docstrings que empiezan por «Create a signed token…» y la prueba
#: señalaba ficheros que no tocan SQL.
#:
#: Una prueba con falsos positivos se desactiva en cuanto estorba, y entonces
#: deja de proteger. La precisión aquí es parte de que la regla dure.
ESCRITURA = re.compile(
    r"\b(INSERT\s+INTO|DELETE\s+FROM|DROP\s+(TABLE|INDEX|SCHEMA)"
    r"|TRUNCATE\s+TABLE|ALTER\s+TABLE|CREATE\s+(TABLE|INDEX)"
    r"|UPDATE\s+\w+\s+SET)\b",
    re.I,
)

#: Excepción única y justificada: `core/pinot/secuencia.py` escribe contra un
#: **SQLite local** (`secuencias.sqlite3`), no contra Pinot. Existe porque Pinot
#: no sabe entregar identificadores únicos bajo concurrencia, y el `UPDATE …
#: RETURNING` de SQLite sí.
#:
#: Está enumerada a mano y no por patrón a propósito: cada excepción nueva debe
#: ser una decisión consciente, no algo que encaje por accidente en una regla
#: amplia.
EXCEPCIONES = {
    "core/pinot/secuencia.py",
}


def _ficheros_de_codigo():
    for directorio in AMBITO:
        for ruta in (RAIZ / directorio).rglob("*.py"):
            texto = str(ruta.relative_to(RAIZ)).replace("\\", "/")
            if "__pycache__" in texto or "/tests/" in texto or texto.startswith("tests/"):
                continue
            yield texto, ruta


def test_ninguna_ruta_de_codigo_escribe_sql_contra_pinot():
    """El único canal de escritura es Kafka.

    Si esta prueba falla con una excepción legítima —otro almacén local, una
    migración— hay que **añadirla a `EXCEPCIONES` con su justificación**, no
    relajar el patrón. Relajarlo dejaría pasar también la escritura que la regla
    existe para impedir.
    """
    hallazgos = []

    for texto, ruta in _ficheros_de_codigo():
        if texto in EXCEPCIONES:
            continue
        contenido = ruta.read_text(encoding="utf-8", errors="replace")
        for numero, linea in enumerate(contenido.splitlines(), 1):
            desnuda = linea.strip()
            if desnuda.startswith("#"):
                continue
            if ESCRITURA.search(linea):
                hallazgos.append(f"{texto}:{numero}  {desnuda[:90]}")

    assert not hallazgos, (
        "Sentencias de escritura SQL fuera del canal Kafka (PG-OPE-007):\n  "
        + "\n  ".join(hallazgos)
    )


def test_las_excepciones_declaradas_siguen_existiendo():
    """Una excepción a un fichero borrado deja la regla más laxa de lo que dice.

    Es el modo de fallo de toda lista de exclusiones: el fichero desaparece, la
    entrada se queda, y años después nadie sabe qué protegía.
    """
    for texto in EXCEPCIONES:
        assert (RAIZ / texto).exists(), (
            f"La excepción «{texto}» apunta a un fichero que ya no existe. "
            "Retirarla de EXCEPCIONES."
        )


def test_la_excepcion_de_secuencia_sigue_siendo_sqlite():
    """La excepción vale **porque no es Pinot**, no porque sea antigua.

    Si `secuencia.py` pasara a escribir contra Pinot, la entrada en `EXCEPCIONES`
    la volvería invisible — una lista de exclusiones que ya no se comprueba es
    peor que no tener regla, porque aparenta cobertura.
    """
    fuente = (RAIZ / "core/pinot/secuencia.py").read_text(encoding="utf-8")

    assert "import sqlite3" in fuente, (
        "core/pinot/secuencia.py ya no usa SQLite. Su excepción a PG-OPE-007 "
        "dependía de eso: revisar contra qué motor escribe ahora."
    )


def test_existe_un_productor_kafka_que_es_el_canal_real():
    """Control negativo.

    Si no hubiera ningún escritor de Kafka, la prueba de arriba pasaría por la
    razón equivocada: no habría escrituras porque no se escribe nada.
    """
    productores = list((RAIZ / "core" / "repositories").rglob("kafka_writer.py"))
    assert productores, "No se encontró ningún KafkaWriter: ¿por dónde se escribe?"
