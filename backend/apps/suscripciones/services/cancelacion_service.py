"""Alias RF-SUSF-009 — cancelación."""

from apps.suscripciones.services.cancelacion_suscripcion_service import (
    CancelacionError,
    CancelacionSuscripcionService,
)

CancelacionService = CancelacionSuscripcionService

__all__ = ["CancelacionService", "CancelacionSuscripcionService", "CancelacionError"]
