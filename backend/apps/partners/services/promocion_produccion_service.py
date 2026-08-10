"""RF-PON-007 y RF-PON-008 — promocion a produccion (CU-O49).

Proceso DELIBERADAMENTE semiautomatico: el partner pide, una persona aprueba
(SRS L382). No es una limitacion tecnica.

Al rechazar, el partner vuelve a «Pruebas activo», NO a «Registrado»: su acceso
de pruebas sigue funcionando porque es justo donde debe corregir lo que motivo
el rechazo (SRS L384). Y no hay tope de reintentos.
"""

from __future__ import annotations

from typing import Any

from apps.partners.domain_constants import (
    CAMBIO_RECHAZO_PRODUCCION,
    CAMBIO_SOLICITUD_PRODUCCION,
    ENTORNO_PRODUCCION,
    ESTADO_PENDIENTE_APROBACION,
    ESTADO_PRODUCCION_ACTIVA,
    ESTADO_PRUEBAS_ACTIVO,
    EJECUTADO_POR_ADMINISTRADOR,
    EJECUTADO_POR_PARTNER,
)
from apps.partners.services.consulta_partner_service import ConsultaPartnerService
from apps.partners.services.emitir_credencial_service import EmitirCredencialService
from apps.partners.services.partner_notificacion_service import (
    PartnerNotificacionService,
)
from core.repositories.partners.credencial_repository import CredencialRepository
from core.repositories.partners.historial_acceso_repository import (
    HistorialAccesoRepository,
)
from core.repositories.partners.partner_repository import PartnerRepository

DECISION_APROBAR = "aprobar"
DECISION_RECHAZAR = "rechazar"


class PromocionProduccionError(Exception):
    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(detail)


class PromocionProduccionService:
    def __init__(
        self,
        partners: PartnerRepository | None = None,
        credenciales: CredencialRepository | None = None,
        historial: HistorialAccesoRepository | None = None,
        consulta: ConsultaPartnerService | None = None,
        emision: EmitirCredencialService | None = None,
        notificaciones: PartnerNotificacionService | None = None,
    ):
        self.partners = partners or PartnerRepository()
        self.credenciales = credenciales or CredencialRepository()
        self.historial = historial or HistorialAccesoRepository()
        self.consulta = consulta or ConsultaPartnerService()
        self.emision = emision or EmitirCredencialService()
        self.notificaciones = notificaciones or PartnerNotificacionService()

    def _partner_y_estado(self, idpartner: int) -> tuple[dict[str, Any], str]:
        partner = self.partners.find_by_id(idpartner)
        if not partner:
            raise PromocionProduccionError("not_found", "Partner no encontrado")
        creds = self.credenciales.list_by_partner(idpartner)
        ultimo = self.historial.ultimo_evento(idpartner)
        return partner, self.consulta.derivar_estado(partner, creds, ultimo)

    def solicitar(
        self, *, idpartner: int, nombre_credencial: str
    ) -> dict[str, Any]:
        """RF-PON-007 — la inicia el partner. NO emite credencial alguna."""
        if not str(nombre_credencial or "").strip():
            raise PromocionProduccionError(
                "validation_error", "nombre_credencial es obligatorio"
            )

        partner, estado = self._partner_y_estado(idpartner)
        if not partner.get("activo", False):
            raise PromocionProduccionError(
                "partner_suspendido", "No se puede solicitar producción estando suspendido"
            )

        # RN-PON-004 — ruta obligatoria, sin atajos: hay que haber pasado por
        # el entorno de pruebas.
        if estado != ESTADO_PRUEBAS_ACTIVO:
            raise PromocionProduccionError(
                "ruta_invalida",
                f"La solicitud requiere estar en «{ESTADO_PRUEBAS_ACTIVO}»; "
                f"el partner está en «{estado}». No se puede solicitar producción "
                "sin haber pasado por el entorno de pruebas",
            )

        self.historial.registrar(
            idpartner=idpartner,
            tipo_cambio=CAMBIO_SOLICITUD_PRODUCCION,
            ejecutado_por=EJECUTADO_POR_PARTNER,
            motivo=nombre_credencial.strip(),
            estado_anterior=ESTADO_PRUEBAS_ACTIVO,
            estado_nuevo=ESTADO_PENDIENTE_APROBACION,
        )

        # Despues de la bitacora, nunca antes: el estado autoritativo es el
        # evento registrado. El aviso es fail-open (RF-PON-007) — si el correo
        # falla, la solicitud sigue pendiente y visible en el panel.
        self.notificaciones.notificar_solicitud_pendiente(
            partner=partner, nombre_credencial=nombre_credencial.strip()
        )
        return {"idpartner": idpartner, "estado": ESTADO_PENDIENTE_APROBACION}

    def resolver(
        self, *, idpartner: int, decision: str, motivo: str | None = None
    ) -> dict[str, Any]:
        """RF-PON-008 — exclusivo del Administrador (el permiso lo aplica la vista)."""
        if decision not in (DECISION_APROBAR, DECISION_RECHAZAR):
            raise PromocionProduccionError(
                "validation_error", "decision debe ser 'aprobar' o 'rechazar'"
            )

        partner, estado = self._partner_y_estado(idpartner)
        if estado != ESTADO_PENDIENTE_APROBACION:
            raise PromocionProduccionError(
                "sin_solicitud_pendiente",
                f"El partner no tiene una solicitud pendiente (está en «{estado}»)",
            )

        if decision == DECISION_RECHAZAR:
            return self._rechazar(partner, motivo)
        return self._aprobar(partner)

    def _rechazar(self, partner: dict[str, Any], motivo: str | None) -> dict[str, Any]:
        idpartner = int(partner["idpartner"])
        # RN-PON-007 — el motivo es obligatorio: se notifica al contacto tecnico
        # y es lo que le permite corregir.
        if not str(motivo or "").strip():
            raise PromocionProduccionError(
                "motivo_requerido", "El rechazo exige un motivo, que se notifica al partner"
            )

        self.historial.registrar(
            idpartner=idpartner,
            tipo_cambio=CAMBIO_RECHAZO_PRODUCCION,
            ejecutado_por=EJECUTADO_POR_ADMINISTRADOR,
            motivo=motivo.strip(),
            estado_anterior=ESTADO_PENDIENTE_APROBACION,
            # Vuelve a «Pruebas activo», NO a «Registrado»: su acceso de pruebas
            # sigue vivo porque es donde debe corregir. Sin tope de reintentos.
            estado_nuevo=ESTADO_PRUEBAS_ACTIVO,
        )

        # RN-PON-007 — el motivo llega al contacto tecnico; sin el, el rechazo
        # es inaccionable y el partner reintentaria lo mismo.
        self.notificaciones.notificar_rechazo(partner=partner, motivo=motivo.strip())
        return {
            "idpartner": idpartner,
            "estado": ESTADO_PRUEBAS_ACTIVO,
            "motivo": motivo.strip(),
        }

    def _aprobar(self, partner: dict[str, Any]) -> dict[str, Any]:
        idpartner = int(partner["idpartner"])
        # El nombre pedido en la solicitud viaja en el `motivo` de su evento.
        solicitud = next(
            (
                ev
                for ev in self.historial.list_by_partner(idpartner)
                if ev.get("tipo_cambio") == CAMBIO_SOLICITUD_PRODUCCION
            ),
            None,
        )
        nombre = (solicitud or {}).get("motivo") or "produccion"

        credencial = self.emision.emitir(
            idpartner=idpartner,
            nombre_credencial=nombre,
            entorno=ENTORNO_PRODUCCION,
            ejecutado_por=EJECUTADO_POR_ADMINISTRADOR,
        )

        # El aviso NUNCA lleva el secreto (RN-PON-005): solo confirma la emision.
        self.notificaciones.notificar_aprobacion(
            partner=partner, nombre_credencial=nombre
        )

        # RN-PON-008 — la credencial de pruebas NO se toca: el partner sigue
        # necesitandola para probar cambios futuros.
        return {
            "idpartner": idpartner,
            "estado": ESTADO_PRODUCCION_ACTIVA,
            "credencial": credencial,
        }
