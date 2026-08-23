"""RF-SUSF-007 — mora: suspensión y regularización."""

from __future__ import annotations

from typing import Any

from core.pinot.tiempo import ahora_ms
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
        # Filtro en SQL y LIMIT explícito: sin `LIMIT`, Pinot recorta a 10 filas de la
        # tabla entera y la factura fallida de este cliente podía no aparecer, dejándolo
        # suspendido sin nada que regularizar.
        rows = self.facturas.pinot.query(
            "SELECT * FROM Fact_Factura WHERE id_suscripcion = %(id_suscripcion)s "
            "AND estado_pago = %(estado)s ORDER BY fecha_emision DESC LIMIT %(limit)s",
            {"id_suscripcion": id_suscripcion, "estado": "Fallida", "limit": 100},
        )
        return rows[0] if rows else None

    def suspender_por_factura(self, factura: dict[str, Any]) -> dict[str, Any] | None:
        """Suspende y **sella el instante**.

        ⚠️ Hasta el 2026-08-23 solo se cambiaba `estado`. `Fact_Suscripcion` es
        una foto que se sobrescribe, así que el momento de la suspensión no
        quedaba en ninguna parte: `hecho_suscripcion` publicaba
        `fecha_suspension` y `fecha_reactivacion` **fijadas a `None` en código**,
        y el informe de suspensión y reactivación no podía contar ni una.
        """
        sus = self.suscripciones.find_by_id(factura["id_suscripcion"])
        if not sus:
            return None
        return self.suscripciones.update(
            sus["id_suscripcion"],
            {"estado": "Suspendida", "fechasuspension": ahora_ms()},
        )

    def regularizar(self, *, id_suscripcion: int) -> dict[str, Any]:
        sus = self.suscripciones.find_by_id(id_suscripcion)
        if not sus or sus.get("estado") != "Suspendida":
            return {"estado_pago": None, "estado_suscripcion": sus.get("estado") if sus else None}
        factura = self.factura_vigente_fallida(id_suscripcion)
        if not factura:
            return {"estado_pago": None, "estado_suscripcion": "Suspendida"}
        # Se reabre la factura a Pendiente y se cobra sobre ESA copia en memoria.
        # Releerla por id devolvía la versión anterior mientras Pinot ingería, con
        # `estado_pago = "Fallida"`, y el cobro salía por la guarda de "no está
        # Pendiente" sin intentar nada: el cliente suspendido no podía regularizar
        # nunca, que es justo lo que el SRS §3.3.1 quiere evitar.
        reabierta = self.facturas.update_from(factura, {"estado_pago": "Pendiente"})
        metodo = self.metodos.find_activo(sus["idcliente"])
        mid = metodo["idmetodopago"] if metodo else "none"
        key = f"{factura['id_factura']}-reactivacion-{mid}"
        updated = self.cobro.intentar_factura(reabierta, idempotency_override=key)
        if updated.get("estado_pago") == "Pagada":
            # ⚠️ La reactivación es el otro extremo del par. Sin sellarla, el
            # informe podría contar suspensiones y nunca una vuelta, que es
            # justo la mitad que interesa: cuántos de los suspendidos vuelven.
            self.suscripciones.update(
                id_suscripcion,
                {"estado": "Activa", "fechareactivacion": ahora_ms()},
            )
            return {
                "estado_pago": "Pagada",
                "estado_suscripcion": "Activa",
                "resultado_ultimo_reintento": updated.get("resultado_ultimo_reintento"),
            }
        if updated.get("estado_pago") != "Fallida":
            self.facturas.update_from(updated, {"estado_pago": "Fallida"})
        return {
            "estado_pago": "Fallida",
            "estado_suscripcion": "Suspendida",
            "resultado_ultimo_reintento": updated.get("resultado_ultimo_reintento"),
        }
