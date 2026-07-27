"""RF-SUSF-009 — cancelación (activo=false, estado Cancelada, fecha_fin)."""

from __future__ import annotations

from typing import Any

from core.repositories.suscripciones.suscripcion_repository import SuscripcionRepository


class CancelacionError(Exception):
    def __init__(self, code: str, detail: str, http_status: int = 400):
        self.code = code
        self.detail = detail
        self.http_status = http_status
        super().__init__(detail)


class CancelacionSuscripcionService:
    def __init__(self, suscripciones: SuscripcionRepository | None = None):
        self.suscripciones = suscripciones or SuscripcionRepository()

    def cancelar(self, *, idcliente: int, motivocancelacion: str = "") -> dict[str, Any]:
        sus = self.suscripciones.find_activa_by_cliente(idcliente)
        if not sus:
            raise CancelacionError("not_found", "Sin suscripción activa", 404)
        if sus.get("estado") == "Cancelada":
            raise CancelacionError("already_cancelled", "Ya cancelada")
        if not motivocancelacion or not str(motivocancelacion).strip():
            raise CancelacionError("validation_error", "motivocancelacion requerido")
        return self.suscripciones.cancelar(
            sus["id_suscripcion"], motivocancelacion=motivocancelacion.strip()
        )
