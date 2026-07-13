"""Access control for onboarding operations."""

from __future__ import annotations

from apps.cuentas_clientes.services.cuenta_access_service import (
    CuentaAccessError,
    CuentaAccessService,
)


class OnboardingAccessError(CuentaAccessError):
    """Access denied for onboarding resource."""


class OnboardingAccessService:
    """Authorization rules for incorporacion-clientes."""

    ADMIN_ROLE = "Administrador"
    CLIENTE_ROLE = "Cliente"

    def __init__(self, access: CuentaAccessService | None = None):
        self.access = access or CuentaAccessService()

    def require_admin_global(self, roles: list[str]) -> None:
        try:
            self.access.require_admin_global(roles)
        except CuentaAccessError as exc:
            raise OnboardingAccessError(str(exc)) from exc

    def require_admin_local(
        self, *, user_id: int, roles: list[str], cliente_id: int
    ) -> None:
        if self.ADMIN_ROLE in roles:
            return
        if self.CLIENTE_ROLE in roles:
            try:
                self.access.require_admin_local(user_id=user_id, cliente_id=cliente_id)
            except CuentaAccessError as exc:
                raise OnboardingAccessError(str(exc)) from exc
            return
        raise OnboardingAccessError("Privilegios insuficientes")

    def require_invitacion_access(
        self, *, user_id: int, roles: list[str], cliente_id: int
    ) -> None:
        if self.ADMIN_ROLE in roles:
            return
        if self.CLIENTE_ROLE in roles:
            try:
                self.access.require_admin_local(user_id=user_id, cliente_id=cliente_id)
            except CuentaAccessError as exc:
                raise OnboardingAccessError(str(exc)) from exc
            return
        raise OnboardingAccessError("Privilegios insuficientes")
