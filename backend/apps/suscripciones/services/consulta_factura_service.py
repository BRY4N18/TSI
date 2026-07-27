"""Alias RF-SUSF-006 — historial/consulta de facturas."""

from apps.suscripciones.services.historial_factura_service import HistorialFacturaService

ConsultaFacturaService = HistorialFacturaService

__all__ = ["ConsultaFacturaService", "HistorialFacturaService"]
