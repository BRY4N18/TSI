"""Registro de cuenta service — CU-O01."""

from __future__ import annotations

import secrets
from typing import Any

from apps.cuentas_clientes.services.audit_service import AuditService
from apps.cuentas_clientes.services.onboarding_access_service import OnboardingAccessService
from apps.cuentas_clientes.services.onboarding_notificacion_service import (
    OnboardingNotificacionService,
)
from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository
from core.repositories.cuentas_clientes.credential_repository import CredentialRepository
from core.repositories.cuentas_clientes.role_repository import RoleRepository
from core.repositories.cuentas_clientes.user_repository import UserRepository

VALID_TIPOS = {"Aseguradora", "Municipio", "Smart City"}
CLIENTE_ROLE = "Cliente"


class RegistroCuentaError(Exception):
    """Account registration failed."""


class RegistroCuentaService:
    """Creates Dim_Cliente, admin local user, credential and role."""

    def __init__(
        self,
        cliente_repo: ClienteRepository | None = None,
        user_repo: UserRepository | None = None,
        credential_repo: CredentialRepository | None = None,
        role_repo: RoleRepository | None = None,
        access: OnboardingAccessService | None = None,
        notificacion: OnboardingNotificacionService | None = None,
        audit: AuditService | None = None,
    ):
        self.cliente_repo = cliente_repo or ClienteRepository()
        self.user_repo = user_repo or UserRepository()
        self.credential_repo = credential_repo or CredentialRepository()
        self.role_repo = role_repo or RoleRepository()
        self.access = access or OnboardingAccessService()
        self.notificacion = notificacion or OnboardingNotificacionService()
        self.audit = audit or AuditService()

    def registrar(
        self,
        *,
        user_id: int,
        roles: list[str],
        data: dict[str, Any],
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        self.access.require_admin_global(roles)

        razon_social = str(data.get("razon_social", "")).strip()
        if len(razon_social) < 2:
            raise RegistroCuentaError("razon_social invalida")

        tipo = data.get("tipo")
        if tipo not in VALID_TIPOS:
            raise RegistroCuentaError("tipo invalido")

        nit = str(data.get("nit_identificacion", "")).strip()
        if not nit:
            raise RegistroCuentaError("nit_identificacion requerido")
        if self.cliente_repo.find_by_nit(nit):
            raise RegistroCuentaError("NIT ya registrado")

        admin = data.get("admin_local") or {}
        gmail = str(admin.get("gmail", "")).strip().lower()
        nombres = str(admin.get("nombres", "")).strip()
        apellidos = str(admin.get("apellidos", "")).strip()
        if not gmail or not nombres or not apellidos:
            raise RegistroCuentaError("admin_local incompleto")
        if self.user_repo.find_by_gmail(gmail):
            raise RegistroCuentaError("Correo ya registrado")

        fecha_inicio = data.get("fecha_inicio_contrato")
        if fecha_inicio is None:
            raise RegistroCuentaError("fecha_inicio_contrato requerida")

        user = self.user_repo.create(
            {
                "nombres": nombres,
                "apellidos": apellidos,
                "gmail": gmail,
                "activo": True,
            }
        )
        temp_password = secrets.token_urlsafe(12)
        self.credential_repo.create_temporary(user["idusuario"], temp_password)

        cliente_role = self.role_repo.find_role_by_name(CLIENTE_ROLE)
        if cliente_role:
            self.role_repo.assign_role_to_user(user["idusuario"], cliente_role["idrol"])

        cliente = self.cliente_repo.create(
            {
                "razon_social": razon_social,
                "nombre": data.get("nombre", ""),
                "tipo": tipo,
                "nit_identificacion": nit,
                "fecha_inicio_contrato": fecha_inicio,
                "admin_local_id": user["idusuario"],
                "estado": "Activo",
            }
        )

        self.audit.log_registro_cuenta(
            user_id=user_id,
            cliente_id=cliente["idcliente"],
            nit=nit,
            ip_address=ip_address,
        )
        self.notificacion.notify_invitacion(
            cliente_id=cliente["idcliente"],
            user_id=user["idusuario"],
            temp_password=temp_password,
            actor_id=user_id,
        )

        return {
            "idcliente": cliente["idcliente"],
            "estado": "Activo",
            "admin_local_id": user["idusuario"],
            "admin_local_gmail": gmail,
            "message": "Cuenta creada",
        }
