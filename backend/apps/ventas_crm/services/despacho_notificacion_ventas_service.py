"""Dispatch notification via core/notificaciones (email/push; slack unavailable)."""
from __future__ import annotations

import logging

from core.notificaciones.email_sender import EmailNotificationSender
from core.notificaciones.push_sender import PushNotificationSender
from core.repositories.ventas_crm.prospecto_repository import ProspectoRepository

logger = logging.getLogger("tsi.ventas_crm.despacho_notificacion")


class CanalNoDisponibleError(Exception):
    pass


class DespachoNotificacionVentasService:
    def __init__(self, email_sender=None, push_sender=None, prospecto_repo=None):
        self.email_sender = email_sender or EmailNotificationSender()
        self.push_sender = push_sender or PushNotificationSender()
        self.prospecto_repo = prospecto_repo or ProspectoRepository()

    def despachar(self, notificacion: dict) -> None:
        canal = notificacion.get("canal")
        if canal == "slack":
            raise CanalNoDisponibleError("canal slack no disponible en MVP")
        if canal == "email":
            prospecto = self.prospecto_repo.find_by_id(int(notificacion["id_prospecto"]))
            gmail = (prospecto or {}).get("gmail") or "noreply@tsi.local"
            # Notify gerente mailbox is resolved via user id in production;
            # email body includes prospect + rule for audit.
            self.email_sender.send(
                event="notificacion_ventas",
                cliente_id=int(notificacion["id_prospecto"]),
                gmail=gmail,
                subject=f"Alerta demo: {notificacion.get('regladisparada')}",
                body=(
                    f"Prospecto {notificacion.get('id_prospecto')} disparó "
                    f"{notificacion.get('regladisparada')} "
                    f"(destinatario usuario {notificacion.get('idusuariogerentenotificado')})."
                ),
            )
            return
        if canal == "push":
            self.push_sender.send(
                event="notificacion_ventas",
                user_id=int(notificacion["idusuariogerentenotificado"]),
                title="Alerta demo",
                body=str(notificacion.get("regladisparada")),
            )
            return
        raise CanalNoDisponibleError(f"canal no soportado: {canal}")
