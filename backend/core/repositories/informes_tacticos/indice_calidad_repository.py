"""Lectura de `indice_calidad_historico` (ClickHouse, solo lectura) — informes tácticos compuestos, US2."""

from __future__ import annotations

from typing import Any

from core.clickhouse.client import ClickHouseClient


class IndiceCalidadRepository:
    def __init__(self, clickhouse: ClickHouseClient | None = None):
        self.clickhouse = clickhouse or ClickHouseClient()

    def consultar(self, desde: str, hasta: str) -> tuple[list[dict[str, Any]] | None, str | None]:
        """Devuelve (serie_completa, ultima_corrida). Serie=None si el DAG nunca corrió."""
        rows = self.clickhouse.query(
            f"""
            SELECT periodo, pct_completitud, pct_descarte, pct_fusion, pct_cobertura_evidencia, indice_consolidado
            FROM indice_calidad_historico
            WHERE periodo >= '{desde}' AND periodo <= '{hasta}'
            ORDER BY periodo
            """
        )
        ultima_rows = self.clickhouse.query("SELECT max(calculado_en) AS ultima FROM indice_calidad_historico")
        ultima_corrida = ultima_rows[0]["ultima"] if ultima_rows else None
        hay_corridas_previas = bool(ultima_rows and ultima_rows[0].get("ultima"))

        if not rows and not hay_corridas_previas:
            return None, None
        return rows, ultima_corrida
