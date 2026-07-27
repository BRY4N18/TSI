"""RF-SUSF-006 — historial de facturas."""

from __future__ import annotations

from typing import Any

from core.repositories.suscripciones.factura_repository import FacturaRepository


class HistorialFacturaService:
    def __init__(self, facturas: FacturaRepository | None = None):
        self.facturas = facturas or FacturaRepository()

    def listar(self, idcliente: int, *, limit: int = 20) -> list[dict[str, Any]]:
        return self.facturas.list_by_cliente(idcliente, limit=limit)

    def detalle(self, idcliente: int, id_factura: str) -> dict[str, Any] | None:
        fac = self.facturas.find_by_id(id_factura)
        if not fac or fac.get("id_cliente") != idcliente:
            return None
        return fac
