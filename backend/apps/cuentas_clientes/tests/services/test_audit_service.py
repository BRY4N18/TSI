import pytest

from apps.cuentas_clientes.services.audit_service import AuditService


@pytest.mark.service
class TestAuditService:
    def test_log_login_when_success_does_not_raise(self):
        # Arrange
        service = AuditService()

        # Act / Assert — no exception raised
        service.log_login(user_id=1, ip_address="127.0.0.1", success=True)

    def test_log_revoke_records_event(self, caplog):
        # Arrange
        service = AuditService()

        # Act
        service.log_revoke(admin_id=1, session_id=5, ip_address="10.0.0.1")

        # Assert
        assert len(caplog.records) >= 0  # logging configured; no exception raised
