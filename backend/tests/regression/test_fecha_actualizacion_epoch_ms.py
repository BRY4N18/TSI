"""Regresión: `fecha_actualizacion` se publica en epoch-ms, nunca en ISO-8601.

Todas las tablas declaran `fecha_actualizacion` como `LONG` con formato
`1:MILLISECONDS:EPOCH`, y en la mayoría es además la **columna de tiempo** de la
tabla y la columna de comparación del upsert.

Publicar ahí una cadena ISO no produce ningún error visible: Pinot **descarta la
fila en silencio**. El repositorio devuelve su payload, la vista responde 201 y
el registro no existe. Fue exactamente lo que pasó con `Dim_Cliente`: el
autorregistro y la conversión de prospecto respondían 201 y la tabla se quedaba
con dos filas viejas — y como `_next_id()` calcula `MAX(idcliente)+1` leyendo de
Pinot, dos altas seguidas recibieron además el **mismo** identificador.

El doble en memoria de la suite no valida tipos, así que ningún test de servicio
puede cazar esto. Este test mira el código fuente: ningún repositorio puede
volver a sellar `fecha_actualizacion` con `isoformat()`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = BACKEND_DIR.parent
REPOSITORIES = BACKEND_DIR / "core" / "repositories"
ESQUEMAS = REPO_DIR / "database" / "esquemas.json"


def test_ningun_repositorio_sella_fecha_actualizacion_con_isoformat():
    infractores = []
    for archivo in REPOSITORIES.rglob("*.py"):
        codigo = archivo.read_text(encoding="utf-8")
        if "fecha_actualizacion" not in codigo:
            continue
        if "isoformat()" in codigo:
            infractores.append(archivo.relative_to(BACKEND_DIR).as_posix())

    assert not infractores, (
        "Estos repositorios escriben `fecha_actualizacion` con `isoformat()`; "
        "Pinot descartaría sus filas en silencio. Usar `core.pinot.tiempo.ahora_ms()`: "
        + ", ".join(sorted(infractores))
    )


def test_ninguna_columna_de_fecha_se_publica_con_cadena_vacia():
    """Una cadena en una columna `LONG` también hace que Pinot tire la fila.

    `UserRepository.create` publicaba `"fechanacimiento": ""` para el alta sin
    fecha de nacimiento. El autorregistro respondía 201, la credencial se creaba
    y el usuario no existía, así que nadie podía entrar con esa cuenta. Para las
    columnas dateTime opcionales se publica `core.pinot.tiempo.SIN_FECHA`.
    """
    esquemas = json.loads(ESQUEMAS.read_text(encoding="utf-8"))
    columnas_fecha = {
        campo["name"]
        for esquema in esquemas
        for campo in esquema.get("dateTimeFieldSpecs", [])
    }

    infractores = []
    for archivo in REPOSITORIES.rglob("*.py"):
        codigo = archivo.read_text(encoding="utf-8")
        for columna in columnas_fecha:
            patron = rf'"{re.escape(columna)}"\s*:\s*(?:data\.get\([^)]*,\s*""\s*\)|"")'
            if re.search(patron, codigo):
                infractores.append(
                    f"{archivo.relative_to(BACKEND_DIR).as_posix()}:{columna}"
                )

    assert not infractores, (
        "Estas columnas de fecha se publican como cadena vacía; Pinot descartaría "
        "la fila entera. Usar `core.pinot.tiempo.SIN_FECHA`: "
        + ", ".join(sorted(infractores))
    )


def test_el_esquema_declara_fecha_actualizacion_como_epoch_ms():
    """La premisa del test anterior: si algún día deja de ser LONG, hay que saberlo."""
    esquemas = json.loads(ESQUEMAS.read_text(encoding="utf-8"))
    desviaciones = []
    for esquema in esquemas:
        for campo in esquema.get("dateTimeFieldSpecs", []):
            if campo["name"] != "fecha_actualizacion":
                continue
            if campo["dataType"] != "LONG" or "MILLISECONDS:EPOCH" not in campo["format"]:
                desviaciones.append(
                    f"{esquema['schemaName']}: {campo['dataType']} {campo['format']}"
                )

    assert not desviaciones, (
        "Tablas cuyo `fecha_actualizacion` ya no es LONG epoch-ms: "
        + ", ".join(sorted(desviaciones))
    )
