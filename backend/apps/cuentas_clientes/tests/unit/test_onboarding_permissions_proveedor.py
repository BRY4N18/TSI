import pytest

from apps.cuentas_clientes.onboarding_permissions import OnboardingPermissions


@pytest.mark.unit
class TestOnboardingPermissionsProveedor:
    def test_can_autorregistrar_is_public(self):
        assert OnboardingPermissions.can_autorregistrar() is True

    def test_can_aprobar_requires_admin(self):
        assert OnboardingPermissions.can_aprobar(["Administrador"]) is True
        assert OnboardingPermissions.can_aprobar(["Cliente"]) is False
