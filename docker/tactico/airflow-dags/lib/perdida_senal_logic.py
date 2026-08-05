"""Lógica pura de detección de huecos de señal GPS (US1, informes compuestos).

Separada del PythonOperator (research.md §4) para poder testear SC-002
(detección correcta de huecos) sin necesitar un scheduler de Airflow real.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def detectar_huecos(pings: list[dict[str, Any]], umbral_seg: int) -> list[dict[str, Any]]:
    """Recorre pings de una única unidad, ordenados por `fechahora` (epoch ms).

    Emite una fila por cada par consecutivo cuyo intervalo excede `umbral_seg`.
    `idaccidente` de la fila de hueco es el del ping posterior al hueco (la
    misión que estaba en curso cuando se recuperó la señal).
    """
    ordenados = sorted(pings, key=lambda p: p["fechahora"])
    huecos = []
    for anterior, siguiente in zip(ordenados, ordenados[1:]):
        intervalo_seg = (siguiente["fechahora"] - anterior["fechahora"]) / 1000
        if intervalo_seg > umbral_seg:
            huecos.append(
                {
                    "idunidademergencia": anterior["idunidademergencia"],
                    "idaccidente": siguiente.get("idaccidente") or anterior.get("idaccidente"),
                    "inicio_hueco": _to_iso(anterior["fechahora"]),
                    "fin_hueco": _to_iso(siguiente["fechahora"]),
                    "duracion_seg": int(intervalo_seg),
                    "umbral_usado_seg": umbral_seg,
                }
            )
    return huecos


def _to_iso(epoch_ms: int) -> str:
    return datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
