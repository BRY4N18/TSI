"""`dim_origen_despacho`: cómo se originó el despacho.

Tres valores en el catálogo del origen: automático, manual y escalado de zona.
La dimensión es pequeña y no cambia, pero **existe como tabla y no como texto
suelto en el hecho** por una razón concreta: el hecho copia el nombre para poder
agrupar sin unir (research D4), y la dimensión conserva la clave para que ese
nombre tenga una autoridad única. Si mañana «Escalado_zona» se renombra, se
renombra en un sitio.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.pinot_http_client import query_pinot

LIMITE = 1_000

CONSULTA = f"SELECT idorigendespacho, origendespacho FROM Dim_OrigenDespacho LIMIT {LIMITE}"


def extraer(consultar: Callable[[str], list[dict]] = query_pinot) -> list[dict]:
    return consultar(CONSULTA)


def construir(filas_origen: Iterable[Mapping[str, Any]], ahora: datetime) -> list[dict]:
    version = ahora.strftime("%Y-%m-%d %H:%M:%S")
    return [
        {
            "idorigendespacho": f["idorigendespacho"],
            # El origen llama a la columna `origendespacho`; el modelo la llama
            # `origen` porque ya vive en una tabla que dice de qué origen habla.
            "origen": f.get("origendespacho") or "",
            "version": version,
        }
        for f in filas_origen
    ]
