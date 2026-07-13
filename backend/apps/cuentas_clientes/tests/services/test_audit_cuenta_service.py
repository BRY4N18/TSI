import pytest

from apps.cuentas_clientes.services.audit_service import AuditService


@pytest.mark.service
class TestAuditCuentaService:
    def test_log_cuenta_field_change_does_not_raise(self, mock_pinot, mock_kafka):
        # Arrange
        audit = AuditService()

        # Act / Assert
        audit.log_cuenta_field_change(
            user_id=3,
            cliente_id=1,
            field="razon_social",
            old_value="A",
            new_value="B",
            ip_address="127.0.0.1",
        )

    def test_log_baja_cuenta_with_motivo_does_not_raise(self, mock_pinot, mock_kafka):
        # Arrange
        audit = AuditService()

        # Act / Assert
        audit.log_baja_cuenta(
            user_id=1,
            cliente_id=1,
            motivo="Cierre contractual",
            ip_address="127.0.0.1",
        )
