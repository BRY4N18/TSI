"""Authentication service — login flow (CU-O05)."""

from __future__ import annotations

from django.conf import settings

from apps.cuentas_clientes.services.audit_service import AuditService
from core.jwt_utils import (
    create_access_token,
    create_refresh_token,
    create_session_token,
)
from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository
from core.repositories.cuentas_clientes.cuenta_usuario_repository import (
    CuentaUsuarioRepository,
)
from core.repositories.cuentas_clientes.credential_repository import (
    ESTADO_CREDENCIAL_CAMBIO_PASSWORD,
    ESTADO_CREDENCIAL_INACTIVO,
    CredentialRepository,
)
from core.repositories.cuentas_clientes.role_repository import RoleRepository
from core.repositories.cuentas_clientes.session_repository import SessionRepository
from core.repositories.cuentas_clientes.user_repository import UserRepository


ESTADO_CLIENTE_BAJA = "Dado de baja"


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
        cliente_repo: ClienteRepository | None = None,
        cuenta_usuario_repo: CuentaUsuarioRepository | None = None,
    ):
        self.user_repo = user_repo or UserRepository()
        self.credential_repo = credential_repo or CredentialRepository()
        self.role_repo = role_repo or RoleRepository()
        self.session_repo = session_repo or SessionRepository()
        self.audit = audit or AuditService()
        self.cliente_repo = cliente_repo or ClienteRepository()
        self.cuenta_usuario_repo = cuenta_usuario_repo or CuentaUsuarioRepository()

    def _cuenta_del_usuario(self, user_id: int) -> dict | None:
        """Cuenta de la que este usuario es administrador local, si la hay.

        Se devuelve en el login para que el cliente con la incorporación
        pendiente pueda ser llevado a su siguiente paso (SRS §3.2.2). Sin este
        dato el asistente de incorporación solo era alcanzable escribiendo la URL.
        """
        cliente = self.cliente_repo.find_by_admin_local(user_id)
        if not cliente:
            return None
        estado = cliente.get("estado_onboarding")
        # Pinot devuelve el centinela `'null'` cuando la columna no tiene valor.
        if estado in (None, "", "null"):
            estado = None
        return {
            "idcliente": int(cliente["idcliente"]),
            "estadoOnboarding": estado,
            "onboardingPendiente": estado is not None and estado != "Completado",
        }

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

        if credential.get("estadocredencial") == ESTADO_CREDENCIAL_INACTIVO:
            self.audit.log_login(user["idusuario"], ip_address, success=False)
            raise AuthenticationError("Credencial inactiva")

        if not self.credential_repo.verify_password(password, credential["contrasena"]):
            self.audit.log_login(user["idusuario"], ip_address, success=False)
            raise AuthenticationError("Credenciales invalidas")

        roles = self.role_repo.get_user_roles(user["idusuario"])
        if not roles:
            self.audit.log_login(user["idusuario"], ip_address, success=False)
            raise AuthenticationError("Usuario sin roles asignados")

        # SRS §3.2.1: el login falla tambien si la organizacion a la que
        # pertenece la persona fue dada de baja. Esta validacion no existia, asi
        # que el personal de un cliente cuyo contrato termino seguia entrando y
        # operando con normalidad.
        cuentas = self.cuenta_usuario_repo.list_cuentas_del_usuario(user["idusuario"])
        if cuentas and all(c.get("estado") == ESTADO_CLIENTE_BAJA for c in cuentas):
            self.audit.log_login(user["idusuario"], ip_address, success=False)
            raise AuthenticationError("Organizacion dada de baja")

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

        requires_password_change = (
            credential.get("estadocredencial") == ESTADO_CREDENCIAL_CAMBIO_PASSWORD
        )
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
            "cuenta": self._cuenta_del_usuario(user["idusuario"]),
        }
