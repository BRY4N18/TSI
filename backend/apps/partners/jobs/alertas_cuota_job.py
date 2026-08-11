"""Job de alertas de cuota (CU-O53, RF-APM-010).

Recorre los partners con cupo asignado, compara su consumo del mes contra el
cupo y emite **un aviso por umbral y periodo**: al 80 % y al 100 %.

Nunca interrumpe el servicio (RN-APM-002). Este job solo lee, avisa y deja
constancia.

Fail-open por partner
---------------------
Un fallo evaluando a un partner no puede impedir que se avise a los demas. Cada
uno se procesa en su propio `try/except`: el job informa de cuantos fallaron,
pero termina su recorrido.
"""

from __future__ import annotations

import logging
from typing import Any

from apps.partners.services.limites_consumo_service import (
    AVISO_CUOTA_80,
    AVISO_CUOTA_100,
    LimitesConsumoService,
)
from apps.partners.services.metricas_consumo_service import MetricasConsumoService
from apps.partners.services.partner_notificacion_service import (
    PartnerNotificacionService,
)
from core.repositories.partners.partner_repository import PartnerRepository

logger = logging.getLogger("tsi.partners.alertas_cuota")

MENSAJE_POR_UMBRAL = {
    AVISO_CUOTA_80: (
        "Has consumido el 80 % de tu cupo mensual de API",
        "Vas por el {llamadas} de {cupo} llamadas incluidas en tu plan este mes.\n\n"
        "Tu servicio NO se interrumpe al superar el cupo: las llamadas de más se "
        "facturan como excedente al cierre del período.",
    ),
    AVISO_CUOTA_100: (
        "Alcanzaste tu cupo mensual de API",
        "Consumiste {llamadas} de las {cupo} llamadas incluidas en tu plan.\n\n"
        "Tu servicio sigue funcionando con normalidad. Las llamadas adicionales "
        "se facturarán como excedente al cierre del período.",
    ),
}


class AlertasCuotaJob:
    def __init__(
        self,
        limites: LimitesConsumoService | None = None,
        partners: PartnerRepository | None = None,
        notificaciones: PartnerNotificacionService | None = None,
        metricas: MetricasConsumoService | None = None,
    ):
        self.limites = limites or LimitesConsumoService()
        self.partners = partners or PartnerRepository()
        self.notificaciones = notificaciones or PartnerNotificacionService()
        self.metricas = metricas or MetricasConsumoService()

    def ejecutar(self, *, desde_ms: int | None = None, hasta_ms: int | None = None) -> dict[str, Any]:
        if desde_ms is None or hasta_ms is None:
            desde_ms, hasta_ms = self.metricas.periodo_actual()

        resumen = {"evaluados": 0, "avisados": 0, "omitidos": 0, "fallidos": 0}
        pagina, _ = self.partners.list(limit=1000)

        for partner in pagina:
            idpartner = int(partner["idpartner"])
            try:
                resumen["evaluados"] += 1
                if self._procesar(idpartner, desde_ms=desde_ms, hasta_ms=hasta_ms):
                    resumen["avisados"] += 1
                else:
                    resumen["omitidos"] += 1
            except Exception:  # noqa: BLE001 — fail-open: un partner no bloquea al resto
                resumen["fallidos"] += 1
                logger.exception("alerta_cuota_fallida", extra={"idpartner": idpartner})

        return resumen

    def _procesar(self, idpartner: int, *, desde_ms: int, hasta_ms: int) -> bool:
        estado = self.limites.evaluar(
            idpartner, desde_ms=desde_ms, hasta_ms=hasta_ms
        )
        if not estado.get("aplica"):
            return False

        umbral = estado.get("umbral_alcanzado")
        if umbral is None:
            return False

        # Un aviso por umbral y periodo: sin esto, el job avisaria en cada
        # ejecucion desde que se cruza el umbral (RN-APM-010).
        if not self.limites.debe_avisar(idpartner, umbral, desde_ms=desde_ms):
            return False

        partner = self.partners.find_by_id(idpartner)
        asunto, cuerpo = MENSAJE_POR_UMBRAL[umbral]
        datos = {"llamadas": estado["llamadas"], "cupo": estado["cupo"]}

        # El aviso va al contacto tecnico del partner y a los Administradores;
        # es fail-open, un buzon caido no impide registrar el aviso.
        self.notificaciones.notificar_cuota(
            partner=partner, asunto=asunto, cuerpo=cuerpo.format(**datos)
        )
        self.limites.registrar_aviso(
            idpartner, umbral, estado["llamadas"], estado["cupo"]
        )
        return True
