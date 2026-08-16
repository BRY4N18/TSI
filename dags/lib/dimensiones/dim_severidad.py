"""`dim_severidad`, con **orden de gravedad**.

El origen guarda la severidad como texto: Leve, Moderado, Grave, Fatal. Ordenar
por ese texto da *Fatal, Grave, Leve, Moderado* — alfabético, y por tanto
absurdo: pone lo más grave junto a lo más leve y separa lo que debería ir
seguido. Un informe ordenado así invita a leer mal la fila más importante.

La columna `orden` existe para que ordenar por gravedad sea ordenar por gravedad.

Qué pasa con una severidad que el catálogo no prevé
---------------------------------------------------
Se le asigna un orden **alto**, no bajo. Así queda al final en vez de colarse
entre lo crítico y lo leve fingiendo una gravedad que nadie determinó.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.pinot_http_client import query_pinot

LIMITE = 1_000

CONSULTA = f"SELECT idseveridad, severidad, descripcion FROM Dim_Severidad LIMIT {LIMITE}"

#: Gravedad creciente, tal como la usa el catálogo del origen.
ORDEN_POR_SEVERIDAD = {"Leve": 1, "Moderado": 2, "Grave": 3, "Fatal": 4}

#: Una severidad fuera del catálogo conocido. Alto a propósito.
ORDEN_NO_CLASIFICADO = 250


def extraer(consultar: Callable[[str], list[dict]] = query_pinot) -> list[dict]:
    return consultar(CONSULTA)


def orden_de(severidad: str | None) -> int:
    return ORDEN_POR_SEVERIDAD.get(severidad or "", ORDEN_NO_CLASIFICADO)


def construir(filas_origen: Iterable[Mapping[str, Any]], ahora: datetime) -> list[dict]:
    version = ahora.strftime("%Y-%m-%d %H:%M:%S")
    return [
        {
            "idseveridad": f["idseveridad"],
            "severidad": f.get("severidad") or "",
            "descripcion": f.get("descripcion"),
            "orden": orden_de(f.get("severidad")),
            "version": version,
        }
        for f in filas_origen
    ]
