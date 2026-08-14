"""RF-O83.2 — marcado de la factura en disputa (contraparte de RF-APM-014).

`api-monitoring-and-billing` dice, textualmente, que una factura marcada como en
disputa **por este módulo** queda excluida del cobro automático y que "al cerrarse
el reclamo vuelve a su estado normal" (RF-APM-014), y que aquel módulo "no abre ni
resuelve disputas: solo respeta la exclusión". Nadie ejecutaba ese marcado: abrir
un ticket sobre una factura la dejaba, para el cobrador, indistinguible de
cualquier otra pendiente, y se le seguía reintentando el cargo al cliente mientras
discutía justamente ese cargo.

El marcado NO se hace escribiendo un flag propio: se usa `estado_pago`, porque es
la columna que ya consultan todos los cobradores —`TarificacionExcedenteService`,
`CobroService`, el dunning y la mora de suscripción— y todos ellos exigen
`'Pendiente'` para cobrar. Con eso, la exclusión es automática y no hay que tocar
ninguno de ellos.
"""

from __future__ import annotations

from core.repositories.suscripciones.factura_repository import FacturaRepository

# Mismo literal que consulta `TarificacionExcedenteService.en_disputa()`.
ESTADO_EN_DISPUTA = "En disputa"
ESTADO_PENDIENTE = "Pendiente"


class DisputaFacturaService:
    def __init__(self, factura_repo: FacturaRepository | None = None):
        self.factura_repo = factura_repo or FacturaRepository()

    def marcar_en_disputa(self, idfactura: str) -> dict | None:
        """Excluye la factura del cobro automático mientras se discute."""
        factura = self.factura_repo.find_by_id(str(idfactura))
        if not factura:
            # El ticket ya quedó registrado: una factura inexistente o aún no
            # visible en Pinot no puede hacer fracasar el reclamo del cliente.
            return None
        if factura.get("estado_pago") == ESTADO_EN_DISPUTA:
            return factura
        return self.factura_repo.update_from(factura, {"estado_pago": ESTADO_EN_DISPUTA})

    def liberar(self, idfactura: str) -> dict | None:
        """Al cerrarse el reclamo la factura vuelve a su estado normal.

        Solo se toca si **sigue** en disputa: si la resolución ya la dejó pagada o
        con el monto ajustado, ese resultado manda y devolverla a «Pendiente»
        volvería a cobrar algo que ya se resolvió.
        """
        factura = self.factura_repo.find_by_id(str(idfactura))
        if not factura or factura.get("estado_pago") != ESTADO_EN_DISPUTA:
            return factura
        return self.factura_repo.update_from(factura, {"estado_pago": ESTADO_PENDIENTE})
