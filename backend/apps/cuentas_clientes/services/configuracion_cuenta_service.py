"""Configuracion de cuenta service — CU-O12."""

from __future__ import annotations

from typing import Any

from apps.cuentas_clientes.services.audit_service import AuditService
from apps.cuentas_clientes.services.onboarding_access_service import OnboardingAccessService
from core.repositories.cuentas_clientes.cliente_repository import ClienteRepository


class ConfiguracionCuentaError(Exception):
    """Account configuration failed."""


class ConfiguracionCuentaService:
    """Sets plan, logo and estado_onboarding=Pendiente."""

    def __init__(
        self,
        cliente_repo: ClienteRepository | None = None,
        access: OnboardingAccessService | None = None,
        audit: AuditService | None = None,
    ):
        self.cliente_repo = cliente_repo or ClienteRepository()
        self.access = access or OnboardingAccessService()
        self.audit = audit or AuditService()

    def configurar(
        self,
        *,
        user_id: int,
        roles: list[str],
        cliente_id: int,
        data: dict[str, Any],
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        self.access.require_admin_global(roles)

        cliente = self.cliente_repo.find_by_id(cliente_id)
        if not cliente:
            raise ConfiguracionCuentaError("Cuenta de cliente no encontrada")

        plan = str(data.get("plan_suscripcion", "")).strip()
        if not plan:
            raise ConfiguracionCuentaError("plan_suscripcion requerido")

        if cliente.get("estado_onboarding") == "Completado":
            raise ConfiguracionCuentaError("Onboarding ya completado")

        updates: dict[str, Any] = {
            "plan_suscripcion": plan,
            "estado_onboarding": "Pendiente",
        }
        logo_url = data.get("logo_url")
        if logo_url is not None:
            if logo_url and not str(logo_url).startswith("https://"):
                raise ConfiguracionCuentaError("logo_url invalida")
            updates["logo_url"] = logo_url

        updated = self.cliente_repo.update(cliente_id, updates)
        if not updated:
            raise ConfiguracionCuentaError("Cuenta de cliente no encontrada")

        self.audit.log_configuracion_cuenta(
            user_id=user_id,
            cliente_id=cliente_id,
            plan_suscripcion=plan,
            ip_address=ip_address,
        )

        return {
            "idcliente": cliente_id,
            "plan_suscripcion": plan,
            "logo_url": updated.get("logo_url"),
            "estado_onboarding": "Pendiente",
        }
