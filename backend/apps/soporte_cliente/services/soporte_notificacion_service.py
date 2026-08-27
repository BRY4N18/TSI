"""Aviso al equipo de soporte cuando entra un ticket nuevo (CU-O83).

Hasta 2026-08-26 registrar un ticket no avisaba a nadie: el ticket quedaba en
`Fact_Reclamo` esperando a que un agente abriera la cola por su cuenta. Ese es
el hallazgo #17 de la revisión del 24/08/2026 —"uno crea el ticket y no le
llega al de soporte"—: técnicamente el agente podía verlo, pero nada se lo
decía.

Fail-open, igual que `AlertaAdminService`: un fallo de SMTP o de resolución de
destinatarios no puede tumbar el alta del ticket. El cliente ya reportó su
incidencia; perder el correo interno es un problema de operación, no una razón
para devolverle un error.
"""

from __future__ import annotations

import logging
from typing import Any

from apps.soporte_cliente.domain_constants import (
    ROL_SOPORTE,
    ROL_SUPERVISOR_SOPORTE,
)
from core.notificaciones.email_sender import EmailNotificationSender, EmailSendError
from core.repositories.cuentas_clientes.role_repository import RoleRepository
from core.repositories.cuentas_clientes.user_repository import UserRepository

logger = logging.getLogger("tsi.soporte.notificacion")

EVENT_TICKET_NUEVO = "soporte_ticket_nuevo"

#: A quién le llega un ticket recién creado.
#:
#: `Administrador` **no está** a propósito: administrar la plataforma no es
#: atender tickets, y la revisión señaló justamente que la gestión de tickets
#: se le estaba mostrando a quien no le corresponde (hallazgo #18).
ROLES_DESTINATARIOS = (ROL_SOPORTE, ROL_SUPERVISOR_SOPORTE)


class SoporteNotificacionService:
    def __init__(
        self,
        role_repo: RoleRepository | None = None,
        user_repo: UserRepository | None = None,
        sender: EmailNotificationSender | None = None,
    ):
        self.roles = role_repo or RoleRepository()
        self.users = user_repo or UserRepository()
        self.sender = sender or EmailNotificationSender()

    def notificar_ticket_nuevo(self, reclamo: dict[str, Any]) -> int:
        """Avisa a cada agente de soporte activo. Retorna cuántos se notificaron."""
        try:
            destinatarios = self._listar_destinatarios()
        except Exception:  # noqa: BLE001 — fail-open
            logger.exception(
                "soporte_notificacion_resolve_failed",
                extra={"id_reclamo": reclamo.get("id_reclamo")},
            )
            return 0

        if not destinatarios:
            # Que no haya nadie con el rol es una condición de operación que hay
            # que poder ver en los logs: significa que los tickets no le llegan
            # a nadie, aunque el alta funcione.
            logger.warning(
                "soporte_notificacion_sin_destinatarios",
                extra={"id_reclamo": reclamo.get("id_reclamo")},
            )
            return 0

        id_reclamo = reclamo.get("id_reclamo")
        prioridad = reclamo.get("prioridad") or "sin clasificar"
        subject = f"[TSI] Ticket #{id_reclamo} — {reclamo.get('asunto', '')}"
        body = (
            f"Entró un ticket nuevo a la cola de soporte.\n\n"
            f"Ticket: #{id_reclamo}\n"
            f"Estado: {reclamo.get('estado')}\n"
            f"Prioridad: {prioridad}\n"
            f"Tipo: {reclamo.get('tipo')}\n"
            f"Asunto: {reclamo.get('asunto')}\n\n"
            f"{reclamo.get('descripcion', '')}\n"
        )

        enviados = 0
        for usuario in destinatarios:
            gmail = usuario.get("gmail")
            if not gmail:
                continue
            try:
                self.sender.send(
                    event=EVENT_TICKET_NUEVO,
                    cliente_id=int(reclamo.get("idcliente") or 0),
                    gmail=str(gmail),
                    subject=subject,
                    body=body,
                )
                enviados += 1
            except EmailSendError:
                logger.exception(
                    "soporte_notificacion_smtp_failed",
                    extra={"id_reclamo": id_reclamo, "idusuario": usuario.get("idusuario")},
                )
            except Exception:  # noqa: BLE001 — fail-open
                logger.exception(
                    "soporte_notificacion_send_failed",
                    extra={"id_reclamo": id_reclamo, "idusuario": usuario.get("idusuario")},
                )
        return enviados

    def _listar_destinatarios(self) -> list[dict[str, Any]]:
        vistos: set[int] = set()
        destinatarios: list[dict[str, Any]] = []
        for rol in ROLES_DESTINATARIOS:
            for uid in self.roles.list_user_ids_for_role(rol):
                if uid in vistos:
                    continue
                vistos.add(uid)
                usuario = self.users.find_by_id(uid)
                if usuario and usuario.get("activo", True) and usuario.get("gmail"):
                    destinatarios.append(usuario)
        return destinatarios
