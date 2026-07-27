"""Thin wrapper — delega al repositorio canónico de suscripciones (Title Case).

Deprecated path: prefer `core.repositories.suscripciones.suscripcion_repository`.
"""

from __future__ import annotations

from core.repositories.suscripciones.suscripcion_repository import (
    SuscripcionRepository as CanonicalSuscripcionRepository,
)


class SuscripcionRepository:
    """Solo-lectura adapter used by soporte SLA (find_idplan_activo)."""

    def __init__(self, pinot=None, kafka=None):
        self._inner = CanonicalSuscripcionRepository(pinot=pinot, kafka=kafka)
        self.pinot = self._inner.pinot

    def find_idplan_activo(self, idcliente: int) -> int | None:
        sus = self._inner.find_activa_by_cliente(idcliente)
        if not sus:
            return None
        if sus.get("estado") != "Activa":
            return None
        return sus.get("idplan")
