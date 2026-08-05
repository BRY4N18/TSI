"""Lógica pura de agregación de rendimiento por proveedor (US3).

MVP: usa el `idcliente` (proveedor) actual de `Dim_UnidadEmergencia` — el
esquema no historiza cambios de proveedor por unidad (sin tabla de tipo SCD),
así que "vigente en el momento del despacho" (Edge Case de la spec) se
aproxima con el proveedor vigente al momento de la corrida del DAG, no con
un snapshot histórico real. Documentado como limitación conocida.
"""

from __future__ import annotations


def agregar_por_proveedor(
    despachos: list[dict],
    historial: list[dict],
    unidades: list[dict],
) -> list[dict]:
    """
    despachos: [{iddespacho, idunidademergencia, periodo, fechahoradespacho, fechahorallegada}]
    historial: [{iddespacho, estadonuevo}]
    unidades: [{idunidademergencia, idcliente}]
    """
    proveedor_por_unidad = {u["idunidademergencia"]: u["idcliente"] for u in unidades}
    proveedor_por_despacho = {
        d["iddespacho"]: proveedor_por_unidad.get(d["idunidademergencia"])
        for d in despachos
    }
    periodo_por_despacho = {d["iddespacho"]: d["periodo"] for d in despachos}

    buckets: dict[tuple, dict] = {}

    def _bucket(iddespacho):
        proveedor = proveedor_por_despacho.get(iddespacho)
        periodo = periodo_por_despacho.get(iddespacho)
        if proveedor is None or periodo is None:
            return None
        key = (periodo, proveedor)
        return buckets.setdefault(
            key,
            {
                "periodo": periodo,
                "idcliente": proveedor,
                "total_despachos": 0,
                "rechazos": 0,
                "abortos": 0,
                "tiempos_llegada": [],
            },
        )

    for d in despachos:
        b = _bucket(d["iddespacho"])
        if b is None:
            continue
        b["total_despachos"] += 1
        if d.get("fechahorallegada") is not None:
            b["tiempos_llegada"].append((d["fechahorallegada"] - d["fechahoradespacho"]) / 1000)

    for h in historial:
        b = _bucket(h["iddespacho"])
        if b is None:
            continue
        if h["estadonuevo"] in ("Rechazado", "Timeout"):
            b["rechazos"] += 1
        elif h["estadonuevo"] == "Abortado":
            b["abortos"] += 1

    resultado = []
    for b in buckets.values():
        total = b["total_despachos"] or 1
        tiempos = b["tiempos_llegada"]
        resultado.append(
            {
                "periodo": b["periodo"],
                "idcliente": b["idcliente"],
                "pct_rechazo": round(b["rechazos"] / total, 4),
                "tiempo_llegada_promedio_seg": round(sum(tiempos) / len(tiempos), 2) if tiempos else 0.0,
                "pct_abortos": round(b["abortos"] / total, 4),
                "total_despachos": b["total_despachos"],
            }
        )
    return resultado
