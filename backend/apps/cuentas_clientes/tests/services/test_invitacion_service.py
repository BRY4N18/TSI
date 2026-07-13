import pytest
from unittest.mock import patch

from apps.cuentas_clientes.services.invitacion_service import InvitacionService


@pytest.mark.service
class TestInvitacionService:
    @patch("apps.cuentas_clientes.services.onboarding_notificacion_service.send_mail")
    def test_reenviar_when_admin_updates_credential(self, mock_send, mock_pinot, mock_kafka):
        # Arrange
        service = InvitacionService()

        # Act
        result = service.reenviar(user_id=1, roles=["Administrador"], cliente_id=1)

        # Assert
        assert result["id_usuario"] == 3
        assert result["message"] == "Invitación reenviada"

    def test_reenviar_when_user_not_in_account_raises(self, mock_pinot, mock_kafka):
        # Arrange
        service = InvitacionService()

        # Act / Assert
        with pytest.raises(Exception, match="pertenece"):
            service.reenviar(
                user_id=1,
                roles=["Administrador"],
                cliente_id=1,
                target_user_id=4,
            )
