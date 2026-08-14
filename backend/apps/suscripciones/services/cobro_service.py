"""RF-SUSF-005 — cobro automático con idempotencia de pasarela."""

from __future__ import annotations

import logging
from typing import Any

from core.repositories.suscripciones.factura_repository import FacturaRepository
from core.repositories.suscripciones.metodo_pago_repository import MetodoPagoRepository
from apps.suscripciones.services.pasarela.simulador_pasarela import SimuladorPasarela

logger = logging.getLogger(__name__)


class CobroService:
    def __init__(
        self,
        facturas: FacturaRepository | None = None,
        metodos: MetodoPagoRepository | None = None,
        pasarela: SimuladorPasarela | None = None,
    ):
        self.facturas = facturas or FacturaRepository()
        self.metodos = metodos or MetodoPagoRepository()
        self.pasarela = pasarela or SimuladorPasarela()

    def intentar(
        self,
        id_factura: str,
        *,
        force_fail: bool = False,
        idempotency_override: str | None = None,
    ) -> dict[str, Any]:
        factura = self.facturas.find_by_id(id_factura)
        if not factura:
            raise ValueError("factura no encontrada")
        return self.intentar_factura(
            factura, force_fail=force_fail, idempotency_override=idempotency_override
        )

    def intentar_factura(
        self,
        factura: dict[str, Any],
        *,
        force_fail: bool = False,
        idempotency_override: str | None = None,
    ) -> dict[str, Any]:
        """Cobra una factura ya en memoria, sin releerla.

        La renovación cobra la factura que acaba de emitir: buscarla por id contra
        Pinot fallaba con "factura no encontrada" durante los 5-15 s que tarda la
        ingesta, y el job entero reventaba.
        """
        id_factura = factura["id_factura"]
        if factura.get("estado_pago") != "Pendiente":
            return factura
        reintentos = int(factura.get("reintentos") or 0)
        metodo = None
        mid = factura.get("idmetodopago")
        if mid:
            metodo = self.metodos.find_by_id(mid)
        if not metodo or not metodo.get("activo"):
            metodo = self.metodos.find_activo(factura["id_cliente"])
        if not metodo:
            return self._fallo(factura, reintentos, "SIN_METODO_PAGO")
        key = idempotency_override or f"{id_factura}-{reintentos}"
        resultado = self.pasarela.cobrar(
            monto=float(factura["monto_total"]),
            tokenpasarela=metodo.get("tokenpasarela", ""),
            idempotency_key=key,
            force_fail=force_fail,
        )
        logger.info(
            "cobro_intento",
            extra={
                "id_factura": id_factura,
                "resultado": resultado.codigo,
                "idempotency_key": key,
            },
        )
        if resultado.exitoso:
            return self.facturas.update_from(
                factura,
                {
                    "estado_pago": "Pagada",
                    "resultado_ultimo_reintento": "Exitoso",
                    "idmetodopago": metodo["idmetodopago"],
                },
            )
        return self._fallo(factura, reintentos, resultado.codigo)

    def _fallo(self, factura: dict[str, Any], reintentos: int, codigo: str) -> dict[str, Any]:
        nuevo = reintentos + 1
        changes: dict[str, Any] = {
            "reintentos": nuevo,
            "resultado_ultimo_reintento": codigo,
        }
        if nuevo >= 3:
            changes["estado_pago"] = "Fallida"
        updated = self.facturas.update_from(factura, changes)
        if nuevo >= 3:
            from apps.suscripciones.services.mora_suscripcion_service import MoraSuscripcionService

            MoraSuscripcionService().suspender_por_factura(factura)
        return updated
