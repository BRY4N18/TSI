"""Autorregistro de proveedor — CU-O14."""

from __future__ import annotations

import secrets
from typing import Any

from apps.cuentas_clientes.services.audit_service import AuditService
from apps.cuentas_clientes.services.onboarding_notificacion_service import (
    OnboardingNotificacionService,
)
from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository
from core.repositories.cuentas_clientes.credential_repository import (
    CredentialRepository,
)
from core.repositories.cuentas_clientes.role_repository import RoleRepository
from core.repositories.cuentas_clientes.user_repository import UserRepository

VALID_TIPOS = {"Proveedor", "Aseguradora", "Municipio", "Smart City"}
CLIENTE_ROLE = "Cliente"
ESTADO_PENDIENTE = "Pendiente_Aprobación"


class AutorregistroProveedorError(Exception):
    """Self-registration failed."""


class AutorregistroProveedorService:
    """Creates Dim_Cliente in Pendiente_Aprobación with admin local credentials."""

    def __init__(
        self,
        cliente_repo: ClienteRepository | None = None,
        user_repo: UserRepository | None = None,
        credential_repo: CredentialRepository | None = None,
        role_repo: RoleRepository | None = None,
        notificacion: OnboardingNotificacionService | None = None,
        audit: AuditService | None = None,
    ):
        self.cliente_repo = cliente_repo or ClienteRepository()
        self.user_repo = user_repo or UserRepository()
        self.credential_repo = credential_repo or CredentialRepository()
        self.role_repo = role_repo or RoleRepository()
        self.notificacion = notificacion or OnboardingNotificacionService()
        self.audit = audit or AuditService()

    def autorregistrar(self, *, data: dict[str, Any], ip_address: str | None = None) -> dict[str, Any]:
        razon_social = str(data.get("razon_social", "")).strip()
        if len(razon_social) < 2:
            raise AutorregistroProveedorError("razon_social invalida")

        tipo = data.get("tipo") or "Proveedor"
        if tipo not in VALID_TIPOS:
            raise AutorregistroProveedorError("tipo invalido")

        nit = str(data.get("nit_identificacion", "")).strip()
        if not nit:
            raise AutorregistroProveedorError("nit_identificacion requerido")
        if self.cliente_repo.find_by_nit(nit):
            raise AutorregistroProveedorError("NIT ya registrado")

        admin = data.get("admin_local") or {}
        gmail = str(admin.get("gmail", "")).strip().lower()
        nombres = str(admin.get("nombres", "")).strip()
        apellidos = str(admin.get("apellidos", "")).strip()
        if not gmail or not nombres or not apellidos:
            raise AutorregistroProveedorError("admin_local incompleto")

        existing_user = self.user_repo.find_by_gmail(gmail)
        temp_password: str | None = None
        if existing_user:
            # find_by_admin_local ignora Rechazado_Anulado → None = libre para reutilizar user
            if self.cliente_repo.find_by_admin_local(existing_user["idusuario"]):
                raise AutorregistroProveedorError("Correo ya registrado")
            user = existing_user
        else:
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
                "fecha_inicio_contrato": data.get("fecha_inicio_contrato"),
                "admin_local_id": user["idusuario"],
                "estado": ESTADO_PENDIENTE,
            }
        )

        self.audit.log_event(
            event_type="autorregistro_proveedor",
            user_id=user["idusuario"],
            ip_address=ip_address,
            result="success",
            details={"idcliente": cliente["idcliente"], "nit": nit, "estado": ESTADO_PENDIENTE},
        )
        if temp_password:
            self.notificacion.notify_invitacion(
                cliente_id=cliente["idcliente"],
                user_id=user["idusuario"],
                temp_password=temp_password,
                actor_id=user["idusuario"],
            )

        return {
            "idcliente": cliente["idcliente"],
            "estado": ESTADO_PENDIENTE,
            "admin_local_id": user["idusuario"],
            "admin_local_gmail": gmail,
            "message": "Solicitud en revisión",
        }
