"""`dim_condado_vecino`: adyacencia física entre condados.

Es la única ampliación de OE3. Desbloquea E3-08 (cobertura de respaldo).
La vecindad es una propiedad **del territorio**, no de un accidente: guardarla
en un hecho la repetiría por cada fila.

Origen: `Dim_CondadoVecino` con `activo = true`. Los nombres se resuelven
contra `Dim_Condado` para no publicar identificadores internos.

La adyacencia no se versiona: si el mapa cambiara, sería otro mapa. El mismo
criterio que `dim_region` aplica a su geografía.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

from lib.dimensiones.desconocido import ETIQUETA_DESCONOCIDA, ID_DESCONOCIDO
from lib.pinot_http_client import query_pinot

LIMITE = 10_000

CONSULTA_VECINOS = (
    f"SELECT idcondado, idcondadovecino FROM Dim_CondadoVecino "
    f"WHERE activo = true LIMIT {LIMITE}"
)
CONSULTA_CONDADOS = (
    f"SELECT idcondado, condado FROM Dim_Condado LIMIT {LIMITE}"
)


def extraer(consultar: Callable[[str], list[dict]] = query_pinot) -> dict[str, list[dict]]:
    return {
        "vecinos": consultar(CONSULTA_VECINOS),
        "condados": consultar(CONSULTA_CONDADOS),
    }


def construir(
    vecinos: Iterable[Mapping[str, Any]],
    condados: Iterable[Mapping[str, Any]],
    ahora: datetime,
) -> list[dict]:
    """Pares activos con nombres resueltos. Un vecino sin catálogo cae en Desconocido."""
    version = ahora.strftime("%Y-%m-%d %H:%M:%S")
    nombres = {
        f["idcondado"]: f.get("condado") or ETIQUETA_DESCONOCIDA
        for f in condados
        if f.get("idcondado") is not None
    }

    filas = []
    for rel in vecinos:
        origen = rel.get("idcondado")
        destino = rel.get("idcondadovecino")
        if origen is None or destino is None:
            continue
        filas.append(
            {
                "idcondado": int(origen),
                "condado": nombres.get(origen, ETIQUETA_DESCONOCIDA),
                "idcondadovecino": (
                    int(destino) if destino in nombres else ID_DESCONOCIDO
                ),
                "condado_vecino": nombres.get(destino, ETIQUETA_DESCONOCIDA),
                "version": version,
            }
        )
    return filas
