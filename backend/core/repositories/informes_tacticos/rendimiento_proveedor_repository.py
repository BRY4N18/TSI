"""Lectura de `rendimiento_por_proveedor` (ClickHouse, solo lectura) — informes tácticos compuestos, US3."""

from __future__ import annotations

from typing import Any

from core.clickhouse.client import ClickHouseClient
from core.pinot.client import PinotClient
from core.repositories.informes_tacticos._catalogo_utils import clientes_by_id


class RendimientoProveedorRepository:
    def __init__(self, clickhouse: ClickHouseClient | None = None, pinot: PinotClient | None = None):
        self.clickhouse = clickhouse or ClickHouseClient()
        self.pinot = pinot or PinotClient()

    def consultar(self, desde: str, hasta: str) -> tuple[list[dict[str, Any]] | None, str | None]:
        # La tabla materializada trae una fila por (periodo, idcliente) — un rango de
        # varios días da varias filas del mismo proveedor si no se agrega aquí.
        # Se pondera por total_despachos de cada día, no un promedio simple de promedios.
        # El alias del agregado no puede reutilizar el nombre de la columna fuente
        # (`total_despachos`): ClickHouse lo sustituye dentro de su propia
        # expresión y lanza ILLEGAL_AGGREGATION — de ahí la subconsulta con
        # `despachos_totales` y el rename en la capa externa.
        rows = self.clickhouse.query(
            f"""
            SELECT
                idcliente,
                despachos_totales AS total_despachos,
                round(_peso_rechazo / despachos_totales, 4) AS pct_rechazo,
                round(_peso_abortos / despachos_totales, 4) AS pct_abortos,
                round(_peso_tiempo / despachos_totales, 2) AS tiempo_llegada_promedio_seg
            FROM (
                SELECT
                    idcliente,
                    sum(total_despachos) AS despachos_totales,
                    sum(pct_rechazo * total_despachos) AS _peso_rechazo,
                    sum(pct_abortos * total_despachos) AS _peso_abortos,
                    sum(tiempo_llegada_promedio_seg * total_despachos) AS _peso_tiempo
                FROM rendimiento_por_proveedor
                WHERE periodo >= '{desde}' AND periodo <= '{hasta}'
                GROUP BY idcliente
            )
            ORDER BY idcliente
            """
        )
        nombres = clientes_by_id(self.pinot, [r["idcliente"] for r in rows])
        for r in rows:
            r["proveedor_nombre"] = nombres.get(r["idcliente"])
        ultima_rows = self.clickhouse.query("SELECT max(calculado_en) AS ultima FROM rendimiento_por_proveedor")
        ultima_corrida = ultima_rows[0]["ultima"] if ultima_rows else None
        hay_corridas_previas = bool(ultima_rows and ultima_rows[0].get("ultima"))

        if not rows and not hay_corridas_previas:
            return None, None
        return rows, ultima_corrida
