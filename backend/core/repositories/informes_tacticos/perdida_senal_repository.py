"""Lectura de `perdida_senal_gps` (ClickHouse, solo lectura) — informes tácticos compuestos, US1."""

from __future__ import annotations

from typing import Any

from core.clickhouse.client import ClickHouseClient
from core.pinot.client import PinotClient
from core.repositories.informes_tacticos._catalogo_utils import unidades_by_id


class PerdidaSenalRepository:
    def __init__(self, clickhouse: ClickHouseClient | None = None, pinot: PinotClient | None = None):
        self.clickhouse = clickhouse or ClickHouseClient()
        self.pinot = pinot or PinotClient()

    def consultar(self, desde: str, hasta: str) -> tuple[list[dict[str, Any]] | None, str | None]:
        """Devuelve (filas, ultima_corrida). Filas=None si el período no fue materializado (FR-008)."""
        rows = self.clickhouse.query(
            f"""
            SELECT idunidademergencia, idaccidente, inicio_hueco, fin_hueco, duracion_seg, umbral_usado_seg
            FROM perdida_senal_gps
            WHERE periodo >= '{desde}' AND periodo <= '{hasta}'
            ORDER BY inicio_hueco
            """
        )
        nombres = unidades_by_id(self.pinot, [r["idunidademergencia"] for r in rows])
        for r in rows:
            info = nombres.get(r["idunidademergencia"], {})
            r["unidad_nombre"] = info.get("nombre")
            r["unidad_placa"] = info.get("placa")

        ultima_corrida_rows = self.clickhouse.query("SELECT max(calculado_en) AS ultima FROM perdida_senal_gps")
        ultima_corrida = ultima_corrida_rows[0]["ultima"] if ultima_corrida_rows else None

        if not rows:
            # Reprocesamiento completo cada corrida (ver perdida_senal_dag.py): si el DAG
            # ya corrió alguna vez, la ausencia de filas en el rango es "sin huecos" (FR-008),
            # no "todavía no procesado" — eso solo pasa si nunca hubo ninguna corrida.
            hay_corridas_previas = bool(ultima_corrida_rows and ultima_corrida_rows[0].get("ultima"))
            if not hay_corridas_previas:
                return None, None
            return [], ultima_corrida

        return rows, ultima_corrida
