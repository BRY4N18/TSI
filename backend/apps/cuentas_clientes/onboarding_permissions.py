"""DRF permission helpers for onboarding endpoints."""

from __future__ import annotations

from apps.cuentas_clientes.services.onboarding_access_service import (
    OnboardingAccessService,
)


class OnboardingPermissions:
    """Static permission checks mirroring onboarding_access_service."""

    _access = OnboardingAccessService()

    @classmethod
    def can_autorregistrar(cls) -> bool:
        """CU-O14 is public (no JWT)."""
        return True

    @classmethod
    def can_aprobar(cls, roles: list[str]) -> bool:
        return OnboardingAccessService.ADMIN_ROLE in roles

    @classmethod
    def can_register(cls, roles: list[str]) -> bool:
        """Legacy CU-O01 — Admin only."""
        return OnboardingAccessService.ADMIN_ROLE in roles

    @classmethod
    def can_configure(cls, roles: list[str]) -> bool:
        """Legacy CU-O12 — Admin only (deprecated for Proveedor)."""
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

    @classmethod
    def can_upload_logo(cls, *, user_id: int, roles: list[str], cliente_id: int) -> bool:
        """Logo solo lo sube el admin_local del cliente (no Admin global)."""
        try:
            cls._access.require_admin_local(
                user_id=user_id, roles=roles, cliente_id=cliente_id
            )
            return True
        except Exception:
            return False
