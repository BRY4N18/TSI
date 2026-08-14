"""Cambio de contrasena temporal por una definitiva — CU-O04.

Cierra el paso que faltaba de RF-AUT-006: la recuperacion generaba la temporal y
el login forzaba el cambio, pero **no existia forma de definir la definitiva**.
El usuario que entraba con una credencial temporal quedaba atrapado en la
pantalla de "solicitar contrasena temporal", que solo le enviaba otra.
"""

from __future__ import annotations

from apps.cuentas_clientes.services.audit_service import AuditService
from core.repositories.cuentas_clientes.credential_repository import (
    ESTADO_CREDENCIAL_CAMBIO_PASSWORD,
    CredentialRepository,
)

LONGITUD_MINIMA = 8


class CambioPasswordError(Exception):
    """El cambio de contrasena no se pudo completar."""

    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(detail)


class CambioPasswordService:
    def __init__(
        self,
        credential_repo: CredentialRepository | None = None,
        audit: AuditService | None = None,
    ):
        self.credential_repo = credential_repo or CredentialRepository()
        self.audit = audit or AuditService()

    def cambiar(
        self,
        *,
        user_id: int,
        password_actual: str,
        password_nueva: str,
        ip_address: str | None = None,
    ) -> dict:
        credencial = self.credential_repo.find_by_user_id(user_id)
        if not credencial:
            raise CambioPasswordError("not_found", "Credencial no encontrada")

        # Se exige la contrasena vigente aunque la sesion ya este autenticada:
        # sin ella, un token robado bastaria para apropiarse de la cuenta.
        if not self.credential_repo.verify_password(
            password_actual, credencial["contrasena"]
        ):
            self.audit.log_event(
                event_type="cambio_password",
                user_id=user_id,
                ip_address=ip_address,
                result="failure",
                details={"motivo": "password_actual_incorrecta"},
            )
            raise CambioPasswordError("unauthorized", "La contrasena actual no es correcta")

        if len(password_nueva or "") < LONGITUD_MINIMA:
            raise CambioPasswordError(
                "validation_error",
                f"La contrasena nueva debe tener al menos {LONGITUD_MINIMA} caracteres",
            )

        if self.credential_repo.verify_password(password_nueva, credencial["contrasena"]):
            raise CambioPasswordError(
                "validation_error", "La contrasena nueva debe ser distinta de la actual"
            )

        actualizada = self.credential_repo.activate_credential(user_id, password_nueva)
        if not actualizada:
            raise CambioPasswordError("not_found", "Credencial no encontrada")

        self.audit.log_event(
            event_type="cambio_password",
            user_id=user_id,
            ip_address=ip_address,
            result="success",
            details={"era_temporal": credencial.get("estadocredencial")
                     == ESTADO_CREDENCIAL_CAMBIO_PASSWORD},
        )
        return {
            "idusuario": user_id,
            "estadocredencial": actualizada["estadocredencial"],
            "message": "Contrasena actualizada",
        }
