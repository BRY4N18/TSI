"""Lectura de Fact_Suscripcion — fuente de verdad del `idplan` vigente del cliente.

research.md Decision 5: no usar `Dim_Cliente.plan_suscripcion` (STRING de
conveniencia) para resolver el `idplan` — la suscripción activa en
`billing-and-auto-renewal` es la fuente correcta. Repositorio de solo lectura:
este módulo no escribe en `Fact_Suscripcion`.
"""

from __future__ import annotations

from core.pinot.client import PinotClient


class SuscripcionRepository:
    def __init__(self, pinot: PinotClient | None = None):
        self.pinot = pinot or PinotClient()

    def find_idplan_activo(self, idcliente: int) -> int | None:
        rows = self.pinot.query(
            "SELECT * FROM Fact_Suscripcion WHERE idcliente = %(idcliente)s",
            {"idcliente": idcliente},
        )
        activas = [r for r in rows if r.get("activo") and r.get("estado") == "activa"]
        if not activas:
            return None
        activas.sort(key=lambda r: r.get("fecha_inicio", 0), reverse=True)
        return activas[0]["idplan"]
