"""PG-OPE-005 y PG-OPE-008 — reintentos que no duplican, borrados que no borran.

**PG-OPE-005.** Kafka garantiza *al menos una vez*, no *exactamente una vez*: un
reintento de red o un redespliegue del worker republican el mismo evento. Sin
upsert, cada republicación sería una fila más — y el informe contaría dos veces
el mismo accidente sin que nada fallara.

**PG-OPE-008.** El borrado físico en el camino de la API destruye el rastro de
auditoría, y en un sistema que maneja evidencia de accidentes ese rastro es parte
del expediente. Un registro «eliminado» debe dejar de listarse y seguir existiendo.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from django.conf import settings

pytestmark = [pytest.mark.unit, pytest.mark.seguridad]

RAIZ = Path(settings.BASE_DIR).parent
TABLAS = RAIZ / "database" / "tablas.json"


def _definiciones() -> list[dict]:
    crudo = json.loads(TABLAS.read_text(encoding="utf-8"))
    lista = crudo if isinstance(crudo, list) else list(crudo.values())
    return [t for t in lista if isinstance(t, dict)]


# --- PG-OPE-005: republicar no duplica ---------------------------------------


def test_toda_tabla_declara_upsert():
    """Sin `upsertConfig`, una tabla acumula una fila por republicación.

    Es el modo de fallo característico de Kafka: la entrega es *al menos una
    vez*, así que la deduplicación **tiene** que ocurrir en el destino. Una tabla
    sin upsert no da error al duplicar; simplemente cuenta de más.
    """
    sin_upsert = [
        t.get("tableName", "?") for t in _definiciones() if not t.get("upsertConfig")
    ]
    assert not sin_upsert, (
        f"{len(sin_upsert)} tablas sin `upsertConfig`: cada republicación añade "
        f"una fila.\n  {sin_upsert[:10]}"
    )


def test_el_upsert_resuelve_por_fecha_de_actualizacion():
    """Las 79 tablas comparan por `fecha_actualizacion`, sin excepciones.

    **Por qué no vale una fecha de negocio.** `fecha_emision` o `fecha_inicio` no
    cambian cuando el registro se corrige: la corrección llega con el mismo valor
    de comparación y no «gana» por criterio, sino por el desempate del motor.

    Y ese desempate era un accidente favorable, no una garantía: la config viva
    traía `dropOutOfOrderRecord: false`, que hace que **la última ingerida gane
    aunque sea más vieja**. Un evento reentregado con retraso podía devolver la
    fila a un estado anterior, en silencio.

    Migradas las 26 el 2026-08-23 (`changelog.md` C14) sin pérdida de datos.
    """
    por_negocio = [
        f"{t.get('tableName', '?')} -> {(t.get('upsertConfig') or {}).get('comparisonColumn')}"
        for t in _definiciones()
        if (t.get("upsertConfig") or {}).get("comparisonColumn") != "fecha_actualizacion"
    ]

    assert not por_negocio, (
        "Tablas que no comparan por `fecha_actualizacion`:\n  "
        + "\n  ".join(por_negocio)
        + "\n\n  Una fecha de negocio no cambia al corregir el registro, así que "
        "la corrección depende del desempate del motor en vez de un criterio "
        "explícito."
    )


def test_todo_repositorio_que_publica_marca_la_fecha_de_actualizacion():
    """La mitad funcional de la regla, y la que de verdad decide.

    Migrar el `comparisonColumn` no sirve de nada si el código no refresca la
    columna al corregir una fila: la corrección llegaría con el mismo valor que
    la versión anterior y el upsert volvería a depender del orden de llegada,
    que es justo lo que la migración venía a eliminar.

    Verificado el 2026-08-23: **cero** repositorios publican sin ponerla.
    """
    import re

    repos = [
        f
        for f in (Path(settings.BASE_DIR) / "core" / "repositories").rglob("*repository.py")
        if "__pycache__" not in str(f)
    ]
    assert repos, "No se encontró ningún repositorio."

    sin_marca = []
    for fichero in repos:
        fuente = fichero.read_text(encoding="utf-8")
        if not re.search(r"\.publish\(|self\.kafka", fuente):
            continue  # solo lectura: no escribe, no necesita la marca
        if '"fecha_actualizacion"' not in fuente:
            sin_marca.append(str(fichero.relative_to(Path(settings.BASE_DIR))))

    assert not sin_marca, (
        "Repositorios que publican sin marcar `fecha_actualizacion`:\n  "
        + "\n  ".join(sin_marca)
        + "\n\n  Sus filas llegarían con la marca de la versión anterior y el "
        "upsert no podría desempatar."
    )


def test_la_marca_es_siempre_el_instante_actual():
    """Copiar el valor previo dejaría el criterio congelado.

    Una corrección que reutilizara la marca de la fila original tendría el mismo
    valor de comparación: no ganaría por criterio, y volveríamos al problema que
    la migración vino a resolver — con la config ya cambiada y la falsa sensación
    de estar cubiertos.
    """
    import re

    sospechosas = []
    for fichero in (Path(settings.BASE_DIR) / "core" / "repositories").rglob("*repository.py"):
        if "__pycache__" in str(fichero):
            continue
        for linea in fichero.read_text(encoding="utf-8").splitlines():
            hallazgo = re.search(r'"fecha_actualizacion":\s*([^,}]+)', linea)
            if not hallazgo:
                continue
            valor = hallazgo.group(1).strip()
            # `now`, `ahora_ms()` y `self._now_ms()` son instantes; leer el valor
            # de la fila existente no lo es.
            if re.search(r"current|existing|previo|anterior", valor):
                sospechosas.append(f"{fichero.name}: {linea.strip()[:80]}")

    assert not sospechosas, (
        "Marcas que copian el valor previo en vez del instante actual:\n  "
        + "\n  ".join(sospechosas)
    )


def test_el_modo_de_upsert_es_completo():
    """`PARTIAL` fusionaría columnas de eventos distintos.

    El resultado sería una fila que **nunca existió**: mitad de una versión,
    mitad de otra. `FULL` reemplaza la fila entera, que es lo coherente con
    publicar el estado completo en cada evento.
    """
    mal = [
        f"{t.get('tableName', '?')}: {(t.get('upsertConfig') or {}).get('mode')}"
        for t in _definiciones()
        if (t.get("upsertConfig") or {}).get("mode") != "FULL"
    ]
    assert not mal, "Tablas con upsert no-FULL:\n  " + "\n  ".join(mal)


def test_la_columna_de_comparacion_existe_en_el_esquema():
    """Una `comparisonColumn` que no existe deja el upsert sin criterio.

    Pinot no falla al declararla: simplemente no desempata, y vuelve al
    comportamiento de «gana la última que llegó» que la columna venía a evitar.
    """
    esquemas = json.loads((RAIZ / "database" / "esquemas.json").read_text(encoding="utf-8"))
    lista = esquemas if isinstance(esquemas, list) else list(esquemas.values())
    columnas = {}
    for esquema in lista:
        if not isinstance(esquema, dict):
            continue
        nombre = esquema.get("schemaName") or esquema.get("tableName")
        if nombre:
            columnas[nombre] = {
                c["name"]
                for k in ("dimensionFieldSpecs", "metricFieldSpecs", "dateTimeFieldSpecs")
                for c in esquema.get(k, [])
            }

    faltan = []
    for tabla in _definiciones():
        nombre = tabla.get("tableName", "").replace("_REALTIME", "").replace("_OFFLINE", "")
        comparacion = (tabla.get("upsertConfig") or {}).get("comparisonColumn")
        if nombre in columnas and comparacion and comparacion not in columnas[nombre]:
            faltan.append(f"{nombre}.{comparacion}")

    assert not faltan, (
        "Columnas de comparación declaradas que no existen en el esquema:\n  "
        + "\n  ".join(faltan)
    )


# --- PG-OPE-008: la API no borra físicamente ---------------------------------

#: Vistas con método `delete`. Cada una debe desactivar, no destruir.
VISTAS_CON_DELETE = [
    ("apps/cuentas_clientes/views/user_role_views.py", "deactivate_user"),
    ("apps/cuentas_clientes/views/user_role_views.py", "deactivate_role"),
]


def test_ningun_delete_de_la_api_destruye_el_registro():
    """El `DELETE` de la API desactiva; no elimina.

    Se comprueba sobre el código de las vistas: el borrado físico existe en el
    sistema —los scripts de `database/` lo usan— pero **no en el camino que un
    usuario puede alcanzar**.
    """
    import re

    destructivos = []
    for carpeta in ("apps",):
        for ruta in (Path(settings.BASE_DIR) / carpeta).rglob("*.py"):
            texto = str(ruta.relative_to(Path(settings.BASE_DIR))).replace("\\", "/")
            if "/tests/" in texto or "__pycache__" in texto:
                continue
            fuente = ruta.read_text(encoding="utf-8", errors="replace")
            if "def delete(self" not in fuente:
                continue
            for bloque in re.findall(r"def delete\(self.*?(?=\n    def |\nclass |\Z)", fuente, re.S):
                if re.search(r"\b(hard_delete|purge|destroy|remove_row)\b", bloque):
                    destructivos.append(f"{texto}: {bloque.strip()[:80]}")

    assert not destructivos, (
        "Vistas cuyo DELETE destruye el registro:\n  " + "\n  ".join(destructivos)
    )


def test_los_scripts_de_mantenimiento_no_son_alcanzables_desde_la_api():
    """El borrado físico vive en `database/`, fuera del camino de la API.

    Que exista está bien —hace falta para limpiar datos de prueba— pero ninguna
    vista debe importarlo: sería un borrado real a un clic de distancia.
    """
    import re

    prohibidos = ("limpia_datos_prueba", "reset_despachos_demo")
    alcanzables = []

    for ruta in (Path(settings.BASE_DIR) / "apps").rglob("*.py"):
        texto = str(ruta.relative_to(Path(settings.BASE_DIR))).replace("\\", "/")
        if "__pycache__" in texto or "/tests/" in texto:
            continue
        fuente = ruta.read_text(encoding="utf-8", errors="replace")
        for prohibido in prohibidos:
            if re.search(rf"\b{prohibido}\b", fuente):
                alcanzables.append(f"{texto} importa {prohibido}")

    assert not alcanzables, (
        "Scripts de mantenimiento alcanzables desde el código de aplicación:\n  "
        + "\n  ".join(alcanzables)
    )
