"""Dispatch notification via core/notificaciones (email/push; slack unavailable)."""
from __future__ import annotations

import logging

from core.notificaciones.email_sender import EmailNotificationSender
from core.notificaciones.push_sender import PushNotificationSender
from core.repositories.cuentas_clientes.user_repository import UserRepository

logger = logging.getLogger("tsi.ventas_crm.despacho_notificacion")


class CanalNoDisponibleError(Exception):
    pass


class DespachoNotificacionVentasService:
    def __init__(self, email_sender=None, push_sender=None, user_repo=None):
        self.email_sender = email_sender or EmailNotificationSender()
        self.push_sender = push_sender or PushNotificationSender()
        self.user_repo = user_repo or UserRepository()

    def despachar(self, notificacion: dict) -> None:
        canal = notificacion.get("canal")
        if canal == "slack":
            raise CanalNoDisponibleError("canal slack no disponible en MVP")
        if canal == "email":
            # SRS §3.1.2 / RF-O25.2: el destinatario es el ejecutivo asignado
            # (idusuariogerentenotificado en Dim_Usuarios), no el prospecto.
            gerente_id = notificacion.get("idusuariogerentenotificado")
            gerente = self.user_repo.find_by_id(int(gerente_id)) if gerente_id else None
            gmail = (gerente or {}).get("gmail")
            if not gmail:
                logger.warning(
                    "gerente_sin_gmail",
                    extra={"idusuariogerentenotificado": gerente_id},
                )
                raise CanalNoDisponibleError("gerente notificado sin correo registrado")
            self.email_sender.send(
                event="notificacion_ventas",
                cliente_id=int(notificacion["id_prospecto"]),
                gmail=gmail,
                subject=f"Alerta demo: {notificacion.get('regladisparada')}",
                body=(
                    f"Prospecto {notificacion.get('id_prospecto')} disparó "
                    f"{notificacion.get('regladisparada')}."
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
