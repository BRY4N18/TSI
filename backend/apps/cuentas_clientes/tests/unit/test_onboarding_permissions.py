import pytest

from apps.cuentas_clientes.onboarding_permissions import OnboardingPermissions


@pytest.mark.unit
class TestOnboardingPermissions:
    def test_can_register_when_admin_returns_true(self):
        # Act
        result = OnboardingPermissions.can_register(["Administrador"])

        # Assert
        assert result is True

    def test_can_register_when_cliente_returns_false(self):
        # Act
        result = OnboardingPermissions.can_register(["Cliente"])

        # Assert
        assert result is False

    def test_can_complete_etapa_when_admin_local_returns_true(self, mock_pinot, mock_kafka):
        # Act
        result = OnboardingPermissions.can_complete_etapa(
            user_id=3, roles=["Cliente"], cliente_id=1
        )

        # Assert
        assert result is True

    def test_can_complete_etapa_when_not_admin_local_returns_false(
        self, mock_pinot, mock_kafka
    ):
        # Act
        result = OnboardingPermissions.can_complete_etapa(
            user_id=4, roles=["Cliente"], cliente_id=1
        )

        # Assert
        assert result is False
