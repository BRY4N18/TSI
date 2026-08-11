"""Job de corte y facturacion del excedente (CU-O54, RF-APM-011 a 013).

Cada ejecucion hace **dos cosas**:

1. Procesa los cortes pendientes del periodo indicado.
2. Recoge los **reintentos ya vencidos** de intentos anteriores.

Las dos en el mismo paso porque el reintento no es un proceso aparte: es el
mismo corte que vuelve a intentarlo mas tarde. Separarlos obligaria a dos
programaciones que podrian desincronizarse.

Corre **cada hora**, no una vez al mes: los escalones de reintento son de 1 h,
6 h y 24 h, y con una ejecucion mensual el primero llegaria treinta dias tarde.
Es idempotente —la no duplicacion vive en el servicio—, asi que ejecutarlo de
mas no cobra de mas.
"""

from __future__ import annotations

import logging
from typing import Any

from apps.partners.services.tarificacion_excedente_service import (
    TarificacionExcedenteService,
)
from core.repositories.partners.partner_repository import PartnerRepository

logger = logging.getLogger("tsi.partners.facturacion")


class FacturacionExcedenteJob:
    def __init__(
        self,
        tarificacion: TarificacionExcedenteService | None = None,
        partners: PartnerRepository | None = None,
    ):
        self.tarificacion = tarificacion or TarificacionExcedenteService()
        self.partners = partners or PartnerRepository()

    def ejecutar(
        self, *, anio: int, mes: int, ahora_ms: int | None = None
    ) -> dict[str, Any]:
        resumen = {
            "evaluados": 0,
            "emitidas": 0,
            "ya_emitidas": 0,
            "omitidas": 0,
            "no_tarificables": 0,
            "fallidas": 0,
            "reintentos_procesados": 0,
        }

        pagina, _ = self.partners.list(limit=1000)
        for partner in pagina:
            idpartner = int(partner["idpartner"])
            resumen["evaluados"] += 1
            try:
                r = self.tarificacion.emitir(idpartner, anio=anio, mes=mes)
            except Exception:  # noqa: BLE001 — fail-open: un partner no frena el corte
                resumen["fallidas"] += 1
                logger.exception("corte_partner_fallido", extra={"idpartner": idpartner})
                continue
            self._contabilizar(resumen, r)

        resumen["reintentos_procesados"] = self._procesar_reintentos(
            anio=anio, mes=mes, ahora_ms=ahora_ms
        )
        return resumen

    @staticmethod
    def _contabilizar(resumen: dict[str, Any], r: dict[str, Any]) -> None:
        clave = {
            "emitida": "emitidas",
            "ya_emitida": "ya_emitidas",
            "en_disputa": "omitidas",
            "omitida": "omitidas",
            "no_tarificable": "no_tarificables",
            "fallida": "fallidas",
        }.get(r.get("resultado", ""))
        if clave:
            resumen[clave] += 1

    def _procesar_reintentos(
        self, *, anio: int, mes: int, ahora_ms: int | None
    ) -> int:
        """Recoge los intentos vencidos y programa el siguiente escalon.

        Las facturas en disputa ya vienen excluidas por el servicio
        (RF-APM-014): aqui no hay que volver a filtrarlas.
        """
        procesados = 0
        for factura in self.tarificacion.reintentos_vencidos(ahora_ms=ahora_ms):
            procesados += 1
            try:
                self.tarificacion.programar_reintento(
                    factura,
                    factura.get("resultado_ultimo_reintento") or "reintento programado",
                    ahora_ms=ahora_ms,
                )
            except Exception:  # noqa: BLE001
                logger.exception(
                    "reintento_fallido",
                    extra={"id_factura": factura.get("id_factura")},
                )
        return procesados
