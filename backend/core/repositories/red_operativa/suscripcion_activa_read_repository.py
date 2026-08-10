"""Fact_Suscripcion read-only repository (módulo Suscripciones y Facturación).

Usado por alta-unidades para verificar `carga_lote_habilitada` (RF-O40.6):
el gate se resuelve contra el campo congelado en la suscripción activa del
Proveedor, no contra Dim_Plan en vivo — una edición posterior del plan no
debe alterar retroactivamente lo que el proveedor ya contrató (R-04 del SRS).
"""

from __future__ import annotations

from typing import Any

from core.pinot.client import PinotClient


class SuscripcionActivaReadRepository:
    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def find_activa_by_cliente(self, idcliente: int) -> dict[str, Any] | None:
        rows = self.pinot.query(
            """
            SELECT * FROM Fact_Suscripcion
            WHERE idcliente = %(idcliente)s AND activo = true
            ORDER BY fecha_inicio DESC
            LIMIT 1
            """,
            {"idcliente": idcliente},
        )
        return rows[0] if rows else None
