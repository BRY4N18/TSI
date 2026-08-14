"""RF-PON-006 — expira la CREDENCIAL, no el partner (CU-O49).

Dos mecanismos complementarios, y el orden importa:

  * `esta_vencida()` DERIVA el estado de los datos. Es lo que consulta el resto
    del sistema, y funciona aunque el job no haya corrido nunca — fail-safe.
  * `procesar_vencidas()` MATERIALIZA el cambio (`activo=false`) y avisa.

Si la vigencia dependiera solo del job, una caida suya dejaria credenciales
vencidas operativas: un fallo abierto en un control de seguridad.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from apps.partners.domain_constants import (
    CAMBIO_EXPIRACION_SANDBOX,
    EJECUTADO_POR_SISTEMA,
    ESTADO_PLAN_ASIGNADO,
    ESTADO_PRUEBAS_ACTIVO,
    NUNCA_EXPIRA,
    SANDBOX_AVISO_PREVIO_DIAS,
)
from apps.partners.services.partner_notificacion_service import PartnerNotificacionService
from core.repositories.partners.credencial_repository import CredencialRepository
from core.repositories.partners.partner_repository import PartnerRepository
from core.repositories.partners.historial_acceso_repository import (
    HistorialAccesoRepository,
)

AVISO_PREVIO = "aviso_previo_expiracion"

logger = logging.getLogger("tsi.partners")


class ExpiracionCredencialService:
    def __init__(
        self,
        credenciales: CredencialRepository | None = None,
        historial: HistorialAccesoRepository | None = None,
        partners: PartnerRepository | None = None,
        notificacion: PartnerNotificacionService | None = None,
    ):
        self.credenciales = credenciales or CredencialRepository()
        self.historial = historial or HistorialAccesoRepository()
        self.partners = partners or PartnerRepository()
        self.notificacion = notificacion or PartnerNotificacionService()

    @staticmethod
    def _now_ms() -> int:
        return int(datetime.now(timezone.utc).timestamp() * 1000)

    # --- Derivacion (fail-safe, no depende del job) -------------------------

    def esta_vencida(self, credencial: dict[str, Any], ahora_ms: int | None = None) -> bool:
        """Vigencia derivada de los datos.

        Una credencial de produccion lleva el centinela del ano 9999, asi que
        esta comparacion nunca la alcanza — por eso el centinela esta en el
        FUTURO y no en 0.
        """
        ahora = ahora_ms if ahora_ms is not None else self._now_ms()
        return int(credencial.get("fecha_expiracion", NUNCA_EXPIRA)) < ahora

    def esta_utilizable(self, credencial: dict[str, Any], ahora_ms: int | None = None) -> bool:
        """Activa Y no vencida. Es la guarda que debe usar CU-O51 en #08."""
        return bool(credencial.get("activo")) and not self.esta_vencida(credencial, ahora_ms)

    # --- Materializacion + avisos (job) -------------------------------------

    def procesar_vencidas(self, ahora_ms: int | None = None) -> dict[str, Any]:
        """Desactiva las vencidas y registra la expiracion.

        RN-PON-006: expira la credencial, NO el partner. `Dim_Partner.activo`
        no se toca y el plan se conserva, de modo que el partner puede generar
        otra credencial por autoservicio sin repetir el alta.
        """
        ahora = ahora_ms if ahora_ms is not None else self._now_ms()
        expiradas: list[int] = []

        for credencial in self.credenciales.vencidas(ahora):
            idcredencial = int(credencial["idcredencial"])
            self.credenciales.desactivar(idcredencial)
            self.historial.registrar(
                idpartner=int(credencial["idpartner"]),
                tipo_cambio=CAMBIO_EXPIRACION_SANDBOX,
                ejecutado_por=EJECUTADO_POR_SISTEMA,
                idcredencial=idcredencial,
                motivo=str(credencial.get("nombre_credencial", "")),
                estado_anterior=ESTADO_PRUEBAS_ACTIVO,
                estado_nuevo=ESTADO_PLAN_ASIGNADO,
            )
            # El SRS pide avisar "de nuevo al producirse". La bitacora registra
            # que ocurrio, pero no se lo cuenta a nadie: sin este envio el
            # partner descubre el vencimiento cuando su integracion empieza a
            # fallar contra el entorno de pruebas.
            self._avisar(
                idpartner=int(credencial["idpartner"]),
                enviar=lambda partner, nombre: self.notificacion.notificar_vencimiento(
                    partner=partner, nombre_credencial=nombre
                ),
                nombre=str(credencial.get("nombre_credencial", "")),
            )
            expiradas.append(idcredencial)

        return {"expiradas": expiradas, "total": len(expiradas)}

    def avisar_proximas_a_vencer(self, ahora_ms: int | None = None) -> dict[str, Any]:
        """Aviso previo (T-7 por defecto), sin duplicar en el mismo ciclo.

        La no duplicacion se comprueba contra la bitacora, no con un flag en la
        credencial: la bitacora ya es el registro de que se aviso.
        """
        ahora = ahora_ms if ahora_ms is not None else self._now_ms()
        umbral = int(
            (
                datetime.fromtimestamp(ahora / 1000, timezone.utc)
                + timedelta(days=SANDBOX_AVISO_PREVIO_DIAS)
            ).timestamp()
            * 1000
        )
        avisadas: list[int] = []

        for credencial in self.credenciales.todas_activas():
            expira = int(credencial.get("fecha_expiracion", NUNCA_EXPIRA))
            if expira == NUNCA_EXPIRA or not (ahora < expira <= umbral):
                continue
            idpartner = int(credencial["idpartner"])
            idcredencial = int(credencial["idcredencial"])
            if self.historial.existe_evento(
                idpartner, AVISO_PREVIO, motivo=str(idcredencial)
            ):
                continue  # ya avisado en este ciclo de vigencia
            self.historial.registrar(
                idpartner=idpartner,
                tipo_cambio=AVISO_PREVIO,
                ejecutado_por=EJECUTADO_POR_SISTEMA,
                idcredencial=idcredencial,
                motivo=str(idcredencial),
                # El aviso NO cambia el estado del partner.
                estado_anterior=ESTADO_PRUEBAS_ACTIVO,
                estado_nuevo=ESTADO_PRUEBAS_ACTIVO,
            )
            dias = max(
                1,
                round((expira - ahora) / (24 * 60 * 60 * 1000)),
            )
            self._avisar(
                idpartner=idpartner,
                enviar=lambda partner, nombre, d=dias: (
                    self.notificacion.notificar_proximo_vencimiento(
                        partner=partner, nombre_credencial=nombre, dias_restantes=d
                    )
                ),
                nombre=str(credencial.get("nombre_credencial", "")),
            )
            avisadas.append(idcredencial)

        return {"avisadas": avisadas, "total": len(avisadas)}

    def _avisar(self, *, idpartner: int, enviar, nombre: str) -> None:
        """Envia el aviso al contacto tecnico del partner.

        Un fallo de correo NO puede tumbar el job: la expiracion ya esta
        materializada y es un control de seguridad. Se registra y se sigue con
        las demas credenciales.
        """
        try:
            partner = self.partners.find_by_id(idpartner)
            if partner:
                enviar(partner, nombre)
        except Exception:  # noqa: BLE001 - el job debe terminar su barrido
            logger.warning("aviso_expiracion_no_enviado", extra={"idpartner": idpartner})
