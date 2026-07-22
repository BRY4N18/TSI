"""Authentication service — login flow (CU-O05)."""

from __future__ import annotations

from django.conf import settings

from apps.cuentas_clientes.services.audit_service import AuditService
from core.jwt_utils import (
    create_access_token,
    create_refresh_token,
    create_session_token,
)
from core.repositories.cuentas_clientes.credential_repository import (
    CredentialRepository,
)
from core.repositories.cuentas_clientes.role_repository import RoleRepository
from core.repositories.cuentas_clientes.session_repository import SessionRepository
from core.repositories.cuentas_clientes.user_repository import UserRepository


class AuthenticationError(Exception):
    """Authentication failed."""


class AuthService:
    """Handles user login with credential and session creation."""

    def __init__(
        self,
        user_repo: UserRepository | None = None,
        credential_repo: CredentialRepository | None = None,
        role_repo: RoleRepository | None = None,
        session_repo: SessionRepository | None = None,
        audit: AuditService | None = None,
    ):
        self.user_repo = user_repo or UserRepository()
        self.credential_repo = credential_repo or CredentialRepository()
        self.role_repo = role_repo or RoleRepository()
        self.session_repo = session_repo or SessionRepository()
        self.audit = audit or AuditService()

    def login(
        self,
        *,
        gmail: str,
        password: str,
        user_agent: str = "",
        ip_address: str | None = None,
    ) -> dict:
        user = self.user_repo.find_by_gmail(gmail)
        if not user or not user.get("activo", False):
            self.audit.log_login(None, ip_address, success=False)
            raise AuthenticationError("Credenciales invalidas")

        credential = self.credential_repo.find_by_user_id(user["idusuario"])
        if not credential:
            self.audit.log_login(user["idusuario"], ip_address, success=False)
            raise AuthenticationError("Credenciales invalidas")

        if credential.get("estadocredencial") == "Inactivo":
            self.audit.log_login(user["idusuario"], ip_address, success=False)
            raise AuthenticationError("Credencial inactiva")

        if not self.credential_repo.verify_password(password, credential["contrasena"]):
            self.audit.log_login(user["idusuario"], ip_address, success=False)
            raise AuthenticationError("Credenciales invalidas")

        roles = self.role_repo.get_user_roles(user["idusuario"])
        if not roles:
            self.audit.log_login(user["idusuario"], ip_address, success=False)
            raise AuthenticationError("Usuario sin roles asignados")

        session_token = create_session_token()
        refresh_token = create_refresh_token()
        session = self.session_repo.create(
            user_id=user["idusuario"],
            token=session_token,
            navegador=user_agent,
            refresh_token=refresh_token,
        )

        access_token = create_access_token(
            user_id=user["idusuario"],
            roles=roles,
            session_id=session["idsession"],
        )

        requires_password_change = credential.get("estadocredencial") == "Cambio contraseña"
        self.audit.log_login(user["idusuario"], ip_address, success=True)

        return {
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "tokenType": "Bearer",
            "expiresInSeconds": int(settings.JWT_ACCESS_TOKEN_LIFETIME.total_seconds()),
            "profile": {
                "idusuario": user["idusuario"],
                "gmail": user["gmail"],
                "roles": roles,
            },
            "requiresPasswordChange": requires_password_change,
        }
