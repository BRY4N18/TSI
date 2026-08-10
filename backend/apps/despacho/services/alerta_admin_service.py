"""CA-DES-007 / CA-DES-011 — fan-out activo a Administradores sin candidatas.

Fail-open: un fallo de resolución de destinatarios o SMTP nunca debe
interrumpir escalamiento O65 ni reasignación O63.
"""

from __future__ import annotations

import logging
from typing import Any

from core.notificaciones.email_sender import EmailNotificationSender, EmailSendError
from core.repositories.cuentas_clientes.role_repository import RoleRepository
from core.repositories.cuentas_clientes.user_repository import UserRepository

logger = logging.getLogger("tsi.despacho.alerta_admin")

ROL_ADMINISTRADOR = "Administrador"
EVENT_SIN_UNIDADES = "despacho_alerta_sin_unidades"


class AlertaAdminService:
    def __init__(
        self,
        role_repo: RoleRepository | None = None,
        user_repo: UserRepository | None = None,
        sender: EmailNotificationSender | None = None,
    ):
        self.roles = role_repo or RoleRepository()
        self.users = user_repo or UserRepository()
        self.sender = sender or EmailNotificationSender()

    def notificar_sin_unidades(self, *, idaccidente: str, contexto: str) -> int:
        """Envía email a cada Administrador activo. Retorna cantidad notificada."""
        try:
            admins = self.listar_administradores()
        except Exception:  # noqa: BLE001 — fail-open
            logger.exception(
                "alerta_admin_resolve_failed",
                extra={"idaccidente": idaccidente, "contexto": contexto},
            )
            return 0

        subject = f"[TSI] Sin unidades disponibles — {idaccidente}"
        body = (
            f"Alerta crítica de despacho ({contexto}).\n"
            f"Accidente: {idaccidente}\n"
            "No hay unidades candidatas. Se requiere intervención manual.\n"
        )
        enviados = 0
        for admin in admins:
            gmail = admin.get("gmail")
            if not gmail:
                continue
            try:
                self.sender.send(
                    event=EVENT_SIN_UNIDADES,
                    cliente_id=0,
                    gmail=str(gmail),
                    subject=subject,
                    body=body,
                )
                enviados += 1
            except EmailSendError:
                logger.exception(
                    "alerta_admin_smtp_failed",
                    extra={
                        "idaccidente": idaccidente,
                        "contexto": contexto,
                        "idusuario": admin.get("idusuario"),
                    },
                )
            except Exception:  # noqa: BLE001 — fail-open
                logger.exception(
                    "alerta_admin_send_failed",
                    extra={
                        "idaccidente": idaccidente,
                        "contexto": contexto,
                        "idusuario": admin.get("idusuario"),
                    },
                )
        return enviados

    def listar_administradores(self) -> list[dict[str, Any]]:
        """Resuelve usuarios con rol Administrador vía Dim_Rol + Dim_Usuario_Rol."""
        user_ids = self.roles.list_user_ids_for_role(ROL_ADMINISTRADOR)
        admins: list[dict[str, Any]] = []
        for uid in user_ids:
            user = self.users.find_by_id(uid)
            if user and user.get("activo", True) and user.get("gmail"):
                admins.append(user)
        return admins
