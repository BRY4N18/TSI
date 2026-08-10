"""Entrada directa de cliente — CU-O96 (catálogo §5.9, Ventas y CRM)."""
import secrets

from apps.ventas_crm.domain import ConflictError, ValidationError
from apps.ventas_crm.services.conversion_cliente_service import TIPOS_CLIENTE_VALIDOS
from apps.cuentas_clientes.services.onboarding_notificacion_service import (
    OnboardingNotificacionService,
)
from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository
from core.repositories.cuentas_clientes.credential_repository import CredentialRepository
from core.repositories.cuentas_clientes.role_repository import RoleRepository
from core.repositories.cuentas_clientes.user_repository import UserRepository

CLIENTE_ROLE = "Cliente"


class EntradaDirectaService:
    REQUIRED = {"nombre", "razon_social", "tipo", "nit_identificacion"}
    ADMIN_REQUIRED = {"nombres", "apellidos", "gmail"}

    def __init__(self, clientes=None, users=None, credentials=None, roles=None, notificacion=None):
        self.clientes = clientes or ClienteRepository()
        self.users = users or UserRepository()
        self.credentials = credentials or CredentialRepository()
        self.roles = roles or RoleRepository()
        self.notificacion = notificacion or OnboardingNotificacionService()

    def registrar(self, data):
        missing = self.REQUIRED - set(k for k, v in data.items() if v not in (None, ""))
        if missing:
            raise ValidationError(f"Campos requeridos: {', '.join(sorted(missing))}")
        if data["tipo"] not in TIPOS_CLIENTE_VALIDOS:
            raise ValidationError(f"tipo inválido: {data['tipo']}")
        if self.clientes.exists_by_nit_any(data["nit_identificacion"]):
            raise ConflictError("NIT ya registrado")

        admin = data.get("admin_local") or {}
        missing_admin = self.ADMIN_REQUIRED - set(k for k, v in admin.items() if v not in (None, ""))
        if missing_admin:
            raise ValidationError(f"admin_local incompleto: {', '.join(sorted(missing_admin))}")
        gmail = str(admin["gmail"]).strip().lower()
        if self.users.find_by_gmail(gmail):
            raise ConflictError("Correo ya registrado")

        user = self.users.create(
            {
                "nombres": str(admin["nombres"]).strip(),
                "apellidos": str(admin["apellidos"]).strip(),
                "gmail": gmail,
                "activo": True,
            }
        )
        temp_password = secrets.token_urlsafe(12)
        self.credentials.create_temporary(user["idusuario"], temp_password)
        cliente_role = self.roles.find_role_by_name(CLIENTE_ROLE)
        if cliente_role:
            self.roles.assign_role_to_user(user["idusuario"], cliente_role["idrol"])

        cliente_data = {k: v for k, v in data.items() if k != "admin_local"}
        cliente = self.clientes.create(
            {
                **cliente_data,
                "idprospecto": None,
                "admin_local_id": user["idusuario"],
                "estado": "Activo",
                "estado_onboarding": "Pendiente",
            }
        )

        self.notificacion.notify_invitacion(
            cliente_id=cliente["idcliente"],
            user_id=user["idusuario"],
            temp_password=temp_password,
            actor_id=user["idusuario"],
            gmail=gmail,
        )

        return cliente
