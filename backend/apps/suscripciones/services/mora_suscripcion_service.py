"""RF-SUSF-007 — mora: suspensión y regularización."""

from __future__ import annotations

from typing import Any

from core.repositories.suscripciones.factura_repository import FacturaRepository
from core.repositories.suscripciones.metodo_pago_repository import MetodoPagoRepository
from core.repositories.suscripciones.suscripcion_repository import SuscripcionRepository
from apps.suscripciones.services.cobro_service import CobroService


class MoraSuscripcionService:
    def __init__(
        self,
        suscripciones: SuscripcionRepository | None = None,
        facturas: FacturaRepository | None = None,
        metodos: MetodoPagoRepository | None = None,
        cobro: CobroService | None = None,
    ):
        self.suscripciones = suscripciones or SuscripcionRepository()
        self.facturas = facturas or FacturaRepository()
        self.metodos = metodos or MetodoPagoRepository()
        self.cobro = cobro or CobroService(
            facturas=self.facturas, metodos=self.metodos
        )

    def factura_vigente_fallida(self, id_suscripcion: int) -> dict[str, Any] | None:
        rows = list(
            r
            for r in (self.facturas.pinot.query("SELECT * FROM Fact_Factura", {}) or [])
            if r.get("id_suscripcion") == id_suscripcion and r.get("estado_pago") == "Fallida"
        )
        if not rows:
            return None
        rows.sort(key=lambda r: r.get("fecha_emision") or 0, reverse=True)
        return rows[0]

    def suspender_por_factura(self, factura: dict[str, Any]) -> dict[str, Any] | None:
        sus = self.suscripciones.find_by_id(factura["id_suscripcion"])
        if not sus:
            return None
        return self.suscripciones.update(sus["id_suscripcion"], {"estado": "Suspendida"})

    def regularizar(self, *, id_suscripcion: int) -> dict[str, Any]:
        sus = self.suscripciones.find_by_id(id_suscripcion)
        if not sus or sus.get("estado") != "Suspendida":
            return {"estado_pago": None, "estado_suscripcion": sus.get("estado") if sus else None}
        factura = self.factura_vigente_fallida(id_suscripcion)
        if not factura:
            return {"estado_pago": None, "estado_suscripcion": "Suspendida"}
        self.facturas.update(factura["id_factura"], {"estado_pago": "Pendiente"})
        metodo = self.metodos.find_activo(sus["idcliente"])
        mid = metodo["idmetodopago"] if metodo else "none"
        key = f"{factura['id_factura']}-reactivacion-{mid}"
        updated = self.cobro.intentar(
            factura["id_factura"], idempotency_override=key
        )
        if updated.get("estado_pago") == "Pagada":
            self.suscripciones.update(id_suscripcion, {"estado": "Activa"})
            return {
                "estado_pago": "Pagada",
                "estado_suscripcion": "Activa",
                "resultado_ultimo_reintento": updated.get("resultado_ultimo_reintento"),
            }
        if updated.get("estado_pago") != "Fallida":
            self.facturas.update(factura["id_factura"], {"estado_pago": "Fallida"})
        return {
            "estado_pago": "Fallida",
            "estado_suscripcion": "Suspendida",
            "resultado_ultimo_reintento": updated.get("resultado_ultimo_reintento"),
        }
