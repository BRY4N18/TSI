import pytest
from unittest.mock import patch

from apps.cuentas_clientes.services.cuenta_notificacion_service import CuentaNotificacionService


@pytest.mark.service
class TestCuentaNotificacionService:
    @patch("apps.cuentas_clientes.services.cuenta_notificacion_service.send_mail")
    def test_notify_transferencia_does_not_raise(self, mock_send, mock_pinot, mock_kafka):
        # Arrange
        service = CuentaNotificacionService()

        # Act / Assert
        service.notify_transferencia(
            cliente_id=1,
            nuevo_admin_id=4,
            anterior_admin_id=3,
            actor_id=3,
        )
        assert mock_send.call_count == 2
