import pytest

from apps.cuentas_clientes.services.revoke_session_service import (
    ForbiddenRevokeError,
    RevokeSessionService,
)


@pytest.mark.service
class TestRevokeSessionService:
    def test_revoke_when_admin_revokes_active_session(self, mock_pinot, mock_kafka):
        # Arrange
        service = RevokeSessionService()

        # Act
        result = service.revoke(
            session_id=1,
            admin_id=1,
            admin_roles=["Administrador"],
        )

        # Assert
        assert result["sessionId"] == 1
        assert result["status"] == "Expulsado"

    def test_revoke_when_not_admin_raises_forbidden(self, mock_pinot, mock_kafka):
        # Arrange
        service = RevokeSessionService()

        # Act / Assert
        with pytest.raises(ForbiddenRevokeError):
            service.revoke(
                session_id=1,
                admin_id=2,
                admin_roles=["Operador"],
            )
