import pytest

from apps.cuentas_clientes.services.session_validation_service import (
    SessionValidationError,
    SessionValidationService,
)
from core.jwt_utils import create_access_token


@pytest.mark.service
class TestSessionValidationService:
    def test_validate_when_token_and_session_active_returns_claims(self, mock_pinot, mock_kafka):
        # Arrange
        service = SessionValidationService()
        token = create_access_token(user_id=1, roles=["Administrador"], session_id=1)

        # Act
        claims = service.validate_token_and_session(token)

        # Assert
        assert claims["sub"] == "1"
        assert claims["session_id"] == 1

    def test_validate_when_session_closed_raises_error(self, mock_pinot, mock_kafka):
        # Arrange
        from core.repositories.cuentas_clientes.session_repository import SessionRepository

        SessionRepository().close_session(1)
        service = SessionValidationService()
        token = create_access_token(user_id=1, roles=["Administrador"], session_id=1)

        # Act / Assert
        with pytest.raises(SessionValidationError):
            service.validate_token_and_session(token)
