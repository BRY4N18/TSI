import pytest

from core.repositories.soporte.supervisor_soporte_repository import (
    SupervisorSoporteRepository,
)


@pytest.mark.repository
class TestSupervisorSoporteRepository:
    def test_get_supervisor_idusuario_returns_configured_default(self, mock_pinot, mock_kafka):
        # Arrange
        repo = SupervisorSoporteRepository()

        # Act
        idusuario = repo.get_supervisor_idusuario()

        # Assert
        assert idusuario == 2  # settings.SOPORTE_SUPERVISOR_USER_ID default

    def test_get_supervisor_when_configured_returns_user(self, mock_pinot, mock_kafka):
        # Arrange
        repo = SupervisorSoporteRepository()

        # Act
        supervisor = repo.get_supervisor()

        # Assert
        assert supervisor is not None
        assert supervisor["idusuario"] == 2
