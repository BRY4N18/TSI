import pytest

from apps.cuentas_clientes.services.audit_service import AuditService


@pytest.mark.service
class TestAuditOnboardingService:
    def test_log_registro_cuenta_does_not_raise(self, caplog):
        # Arrange
        service = AuditService()

        # Act / Assert
        service.log_registro_cuenta(user_id=1, cliente_id=2, nit="123")

    def test_log_configuracion_cuenta_does_not_raise(self):
        # Arrange
        service = AuditService()

        # Act / Assert
        service.log_configuracion_cuenta(
            user_id=1, cliente_id=2, plan_suscripcion="premium"
        )

    def test_log_onboarding_etapa_does_not_raise(self):
        # Arrange
        service = AuditService()

        # Act / Assert
        service.log_onboarding_etapa(user_id=3, cliente_id=1, etapa="cambio_password")

    def test_log_reenvio_invitacion_does_not_raise(self):
        # Arrange
        service = AuditService()

        # Act / Assert
        service.log_reenvio_invitacion(user_id=1, target_user_id=3, cliente_id=1)

    def test_log_onboarding_reminder_does_not_raise(self):
        # Arrange
        service = AuditService()

        # Act / Assert
        service.log_onboarding_reminder(cliente_id=1, admin_local_id=3)
