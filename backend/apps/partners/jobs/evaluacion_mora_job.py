"""Job diario de mora de excedente de API (CU-O55, RF-PAC-003/004/007).

Recorre los partners ACTIVOS, calcula sus dias de mora y decide: avisar T-10,
avisar T-5, o suspender al superarse el limite.

Por que un job periodico y no un disparador por evento
-------------------------------------------------------
La mora avanza con el TIEMPO, no con eventos: nadie «hace» que pasen diez dias.
Un disparador al cambiar el estado de una factura nunca se ejecutaria el dia que
toca avisar (`research.md` Decision 6).

Este job NUNCA reactiva
------------------------
No tiene rama de reactivacion, y no es un olvido (RN-PAC-009). Si un partner
suspendido paga, la factura desaparece de la condicion de entrada y el job
sencillamente deja de verlo — pero **sigue suspendido** hasta que un
Administrador lo reactive a mano.

Fail-open por partner
---------------------
Un fallo evaluando a uno no puede impedir que se avise a los demas, ni que se
suspenda a un moroso real. Mismo patron que `alertas_cuota_job` de #08.
"""

from __future__ import annotations

import logging
from typing import Any

from apps.partners.services.evaluacion_mora_service import EvaluacionMoraService
from core.repositories.partners.partner_repository import PartnerRepository

logger = logging.getLogger("tsi.partners.evaluacion_mora")


class EvaluacionMoraJob:
    def __init__(
        self,
        mora: EvaluacionMoraService | None = None,
        partners: PartnerRepository | None = None,
    ):
        self.mora = mora or EvaluacionMoraService()
        self.partners = partners or PartnerRepository()

    def ejecutar(self, *, ahora_ms: int | None = None) -> dict[str, Any]:
        resumen = {
            "evaluados": 0,
            "avisados": 0,
            "suspendidos": 0,
            "sin_mora": 0,
            "fallidos": 0,
        }

        cursor = None
        while True:
            pagina, cursor = self.partners.list(limit=200, cursor=cursor)
            for partner in pagina:
                if not partner.get("activo", False):
                    # Ya suspendido: no hay nada mas que cortarle, y este job no
                    # lo reactiva aunque haya pagado.
                    continue
                resumen["evaluados"] += 1
                try:
                    resultado = self.mora.evaluar_partner(partner, ahora_ms=ahora_ms)
                except Exception:  # noqa: BLE001 — fail-open por partner
                    resumen["fallidos"] += 1
                    logger.exception(
                        "Fallo evaluando la mora del partner %s",
                        partner.get("idpartner"),
                    )
                    continue

                accion = resultado.get("accion")
                if accion == "avisado":
                    resumen["avisados"] += 1
                elif accion == "suspendido":
                    resumen["suspendidos"] += 1
                elif accion == "sin_mora":
                    resumen["sin_mora"] += 1
            if not cursor:
                break

        logger.info("Evaluación de mora completada: %s", resumen)
        return resumen
