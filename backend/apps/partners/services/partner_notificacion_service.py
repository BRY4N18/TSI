"""Avisos del onboarding de partners (research.md Decision 11).

Mecanismo reutilizado, no inventado
-----------------------------------
Decision 11 dejaba pendiente *verificar* que canal usar. Verificado: el
proyecto ya tiene `core/notificaciones/email_sender.py` como capa transversal
SMTP, y cada dominio la envuelve con su propio servicio
(`OnboardingNotificacionService`, `AlertaAdminService`). Este servicio sigue
ese mismo patron; no se introduce ningun canal nuevo.

Fail-open, deliberadamente
--------------------------
Ningun metodo propaga excepciones: devuelven cuantos avisos salieron. Un
buzon caido no puede tumbar una promocion a produccion ya aprobada, porque
el estado autoritativo vive en la bitacora, no en el correo. Es la misma
decision que toma `AlertaAdminService` para el escalamiento de despacho.

El destinatario del partner es `contacto_tecnico_gmail`, campo obligatorio de
`Dim_Partner` que existe precisamente para esto.
"""

from __future__ import annotations

import logging
from typing import Any

from core.notificaciones.email_sender import EmailNotificationSender, EmailSendError
from core.repositories.cuentas_clientes.role_repository import RoleRepository
from core.repositories.cuentas_clientes.user_repository import UserRepository

logger = logging.getLogger("tsi.partners.notificacion")

ROL_ADMINISTRADOR = "Administrador"

EVENTO_SOLICITUD_PENDIENTE = "partner_solicitud_produccion_pendiente"
EVENTO_APROBACION = "partner_promocion_aprobada"
EVENTO_RECHAZO = "partner_promocion_rechazada"
EVENTO_CREDENCIAL_EMITIDA = "partner_credencial_emitida"
EVENTO_AVISO_VENCIMIENTO = "partner_credencial_por_vencer"
EVENTO_VENCIMIENTO = "partner_credencial_vencida"


class PartnerNotificacionService:
    def __init__(
        self,
        sender: EmailNotificationSender | None = None,
        role_repo: RoleRepository | None = None,
        user_repo: UserRepository | None = None,
    ):
        self.sender = sender or EmailNotificationSender()
        self.roles = role_repo or RoleRepository()
        self.users = user_repo or UserRepository()

    # --- Avisos al contacto tecnico del partner ------------------------------

    def notificar_aprobacion(self, *, partner: dict[str, Any], nombre_credencial: str) -> int:
        """RF-PON-008 — la promocion fue aprobada y ya hay credencial productiva."""
        return self._enviar_al_partner(
            partner,
            evento=EVENTO_APROBACION,
            subject="Acceso a producción aprobado — Tráfico Seguro Integral",
            body=(
                f"Su solicitud de acceso a producción fue aprobada.\n\n"
                f"Partner: {partner.get('nombrepartner', '')}\n"
                f"Credencial emitida: {nombre_credencial}\n\n"
                "El secreto se muestra una sola vez en el portal, al emitirse, y no "
                "se puede recuperar después. Si lo pierde, emita una credencial nueva: "
                "sus credenciales actuales seguirán funcionando.\n\n"
                "Su credencial de pruebas sigue activa y puede seguir usándola."
            ),
        )

    def notificar_rechazo(self, *, partner: dict[str, Any], motivo: str) -> int:
        """RN-PON-007 — el motivo viaja en el aviso: es lo que permite corregir."""
        return self._enviar_al_partner(
            partner,
            evento=EVENTO_RECHAZO,
            subject="Solicitud de producción rechazada — Tráfico Seguro Integral",
            body=(
                f"Su solicitud de acceso a producción fue rechazada.\n\n"
                f"Partner: {partner.get('nombrepartner', '')}\n"
                f"Motivo: {motivo}\n\n"
                "Su acceso de pruebas sigue activo: corrija lo indicado en ese entorno "
                "y vuelva a solicitar la promoción. No hay límite de reintentos."
            ),
        )

    def notificar_credencial_emitida(
        self, *, partner: dict[str, Any], nombre_credencial: str, entorno: str
    ) -> int:
        """El aviso confirma la emision; el secreto NUNCA viaja por correo."""
        return self._enviar_al_partner(
            partner,
            evento=EVENTO_CREDENCIAL_EMITIDA,
            subject="Nueva credencial de API emitida — Tráfico Seguro Integral",
            body=(
                f"Se emitió una credencial de API para su integración.\n\n"
                f"Nombre: {nombre_credencial}\n"
                f"Entorno: {entorno}\n\n"
                "Por seguridad, el secreto no se envía por correo: solo se muestra "
                "una vez en el portal, en el momento de la emisión.\n\n"
                "Si usted no solicitó esta credencial, contacte al administrador."
            ),
        )

    def notificar_proximo_vencimiento(
        self, *, partner: dict[str, Any], nombre_credencial: str, dias_restantes: int
    ) -> int:
        """RF-PON-009 — aviso previo, para que la rotacion no sea una urgencia."""
        return self._enviar_al_partner(
            partner,
            evento=EVENTO_AVISO_VENCIMIENTO,
            subject=(
                f"Su credencial de pruebas vence en {dias_restantes} días — "
                "Tráfico Seguro Integral"
            ),
            body=(
                f"La credencial «{nombre_credencial}» vencerá en {dias_restantes} días.\n\n"
                "Emita una credencial nueva antes de esa fecha para no interrumpir su "
                "integración. Emitirla no desactiva las que ya tiene.\n\n"
                "Las credenciales de producción no vencen."
            ),
        )

    def notificar_vencimiento(
        self, *, partner: dict[str, Any], nombre_credencial: str
    ) -> int:
        """RF-PON-009 — vencimiento consumado."""
        return self._enviar_al_partner(
            partner,
            evento=EVENTO_VENCIMIENTO,
            subject="Su credencial de pruebas venció — Tráfico Seguro Integral",
            body=(
                f"La credencial «{nombre_credencial}» venció y ya no permite "
                "autenticarse.\n\n"
                "Emita una credencial de pruebas nueva desde el portal para "
                "restablecer su acceso al entorno de pruebas."
            ),
        )

    # --- Aviso a los Administradores -----------------------------------------

    def notificar_solicitud_pendiente(
        self, *, partner: dict[str, Any], nombre_credencial: str
    ) -> int:
        """RF-PON-007 — la aprobacion es humana: alguien tiene que enterarse.

        Sin este aviso la solicitud queda esperando a que un Administrador
        mire el panel por casualidad.
        """
        subject = (
            f"[TSI] Solicitud de acceso a producción — "
            f"{partner.get('nombrepartner', 'partner')}"
        )
        body = (
            f"El partner «{partner.get('nombrepartner', '')}» "
            f"(idpartner {partner.get('idpartner')}) solicitó acceso a producción.\n\n"
            f"Credencial solicitada: {nombre_credencial}\n"
            f"Contacto técnico: {partner.get('contacto_tecnico_nombre', '')} "
            f"<{partner.get('contacto_tecnico_gmail', '')}>\n\n"
            "La solicitud queda pendiente hasta que un Administrador la apruebe "
            "o la rechace con motivo."
        )

        try:
            administradores = self._listar_administradores()
        except Exception:  # noqa: BLE001 — fail-open
            logger.exception(
                "partner_notif_resolve_admins_failed",
                extra={"idpartner": partner.get("idpartner")},
            )
            return 0

        enviados = 0
        for admin in administradores:
            if self._enviar(
                evento=EVENTO_SOLICITUD_PENDIENTE,
                gmail=str(admin["gmail"]),
                idcliente=int(partner.get("idcliente", 0) or 0),
                subject=subject,
                body=body,
            ):
                enviados += 1
        return enviados

    def _listar_administradores(self) -> list[dict[str, Any]]:
        user_ids = self.roles.list_user_ids_for_role(ROL_ADMINISTRADOR)
        return [
            user
            for uid in user_ids
            if (user := self.users.find_by_id(uid))
            and user.get("activo", True)
            and user.get("gmail")
        ]

    # --- Envio -----------------------------------------------------------------

    def _enviar_al_partner(
        self, partner: dict[str, Any], *, evento: str, subject: str, body: str
    ) -> int:
        gmail = str(partner.get("contacto_tecnico_gmail") or "").strip()
        if not gmail:
            logger.warning(
                "partner_notif_sin_destinatario",
                extra={"event": evento, "idpartner": partner.get("idpartner")},
            )
            return 0
        return 1 if self._enviar(
            evento=evento,
            gmail=gmail,
            idcliente=int(partner.get("idcliente", 0) or 0),
            subject=subject,
            body=body,
        ) else 0

    def _enviar(
        self, *, evento: str, gmail: str, idcliente: int, subject: str, body: str
    ) -> bool:
        try:
            self.sender.send(
                event=evento,
                cliente_id=idcliente,
                gmail=gmail,
                subject=subject,
                body=body,
            )
            return True
        except EmailSendError:
            logger.warning("partner_notif_smtp_failed", extra={"event": evento})
            return False
        except Exception:  # noqa: BLE001 — fail-open
            logger.exception("partner_notif_failed", extra={"event": evento})
            return False
