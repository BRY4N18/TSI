"""DRF permission helpers for onboarding endpoints."""

from __future__ import annotations

from apps.cuentas_clientes.services.onboarding_access_service import OnboardingAccessService


class OnboardingPermissions:
    """Static permission checks mirroring onboarding_access_service."""

    _access = OnboardingAccessService()

    @classmethod
    def can_register(cls, roles: list[str]) -> bool:
        return OnboardingAccessService.ADMIN_ROLE in roles

    @classmethod
    def can_configure(cls, roles: list[str]) -> bool:
        return OnboardingAccessService.ADMIN_ROLE in roles

    @classmethod
    def can_complete_etapa(cls, *, user_id: int, roles: list[str], cliente_id: int) -> bool:
        try:
            cls._access.require_admin_local(
                user_id=user_id, roles=roles, cliente_id=cliente_id
            )
            return True
        except Exception:
            return False

    @classmethod
    def can_resend_invitation(
        cls, *, user_id: int, roles: list[str], cliente_id: int
    ) -> bool:
        try:
            cls._access.require_invitacion_access(
                user_id=user_id, roles=roles, cliente_id=cliente_id
            )
            return True
        except Exception:
            return False
