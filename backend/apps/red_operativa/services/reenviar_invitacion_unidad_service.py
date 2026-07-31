"""Reenviar invitación SMTP de login Unidad ligada a una unidad (Proveedor)."""

from __future__ import annotations

import secrets
from typing import Any

from apps.cuentas_clientes.services.onboarding_notificacion_service import (
    OnboardingNotificacionService,
)
from apps.red_operativa.services.proveedor_access_service import ProveedorAccessService
from apps.red_operativa.services.registro_unidad_service import SMTP_FAIL_MSG
from core.repositories.cuentas_clientes.credential_repository import CredentialRepository
from core.repositories.cuentas_clientes.user_repository import UserRepository
from core.repositories.red_operativa.unidad_emergencia_repository import (
    UnidadEmergenciaRepository,
)


class ReenviarInvitacionUnidadService:
    def __init__(
        self,
        unidad_repo: UnidadEmergenciaRepository | None = None,
        access: ProveedorAccessService | None = None,
        user_repo: UserRepository | None = None,
        credential_repo: CredentialRepository | None = None,
        notificacion: OnboardingNotificacionService | None = None,
    ):
        self.unidad_repo = unidad_repo or UnidadEmergenciaRepository()
        self.access = access or ProveedorAccessService()
        self.user_repo = user_repo or UserRepository()
        self.credential_repo = credential_repo or CredentialRepository()
        self.notificacion = notificacion or OnboardingNotificacionService()

    def reenviar(
        self,
        idunidademergencia: int,
        *,
        user_id: int,
        roles: list[str],
    ) -> dict[str, Any]:
        unidad = self.unidad_repo.find_by_id(idunidademergencia)
        if not unidad:
            raise LookupError("Unidad no encontrada")
        cliente = self.access.require_unidad_propia(
            user_id=user_id,
            roles=roles,
            unidad=unidad,
        )
        idusuario = unidad.get("idusuario")
        if not idusuario:
            raise ValueError("La unidad no tiene usuario de login asignado")
        dest = self.user_repo.find_by_id(int(idusuario))
        if not dest or not dest.get("activo", False):
            raise LookupError("Usuario de la unidad no encontrado")
        if not dest.get("gmail"):
            raise ValueError("El usuario de la unidad no tiene gmail")

        temp_password = secrets.token_urlsafe(12)
        cred = self.credential_repo.find_by_user_id(int(idusuario))
        if cred:
            self.credential_repo.reset_password(int(idusuario), temp_password)
        else:
            self.credential_repo.create_temporary(int(idusuario), temp_password)

        enviada = self.notificacion.notify_invitacion(
            cliente_id=int(cliente["idcliente"]),
            user_id=int(idusuario),
            temp_password=temp_password,
            actor_id=user_id,
            gmail=str(dest.get("gmail") or ""),
        )
        result: dict[str, Any] = {
            "idunidademergencia": int(idunidademergencia),
            "idusuario": int(idusuario),
            "invitacion_enviada": bool(enviada),
        }
        if not enviada:
            result["invitacion_error"] = SMTP_FAIL_MSG
        return result
