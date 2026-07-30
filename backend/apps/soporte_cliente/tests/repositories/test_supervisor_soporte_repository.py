import pytest

from core.repositories.soporte.supervisor_soporte_repository import (
    SupervisorSoporteRepository,
)


@pytest.mark.repository
class TestSupervisorSoporteRepository:
    def test_get_supervisor_idusuario_resuelve_por_rol(self, mock_pinot, mock_kafka):
        # Arrange — conftest: usuario 2 tiene idrol=10 (SupervisorSoporte)
        repo = SupervisorSoporteRepository()

        # Act
        idusuario = repo.get_supervisor_idusuario()

        # Assert
        assert idusuario == 2

    def test_get_supervisor_when_rol_asignado_returns_user(self, mock_pinot, mock_kafka):
        # Arrange
        repo = SupervisorSoporteRepository()

        # Act
        supervisor = repo.get_supervisor()

        # Assert
        assert supervisor is not None
        assert supervisor["idusuario"] == 2

    def test_get_supervisor_idusuario_when_varios_prefiere_env(
        self, mock_pinot, mock_kafka, pinot_store, settings
    ):
        # Arrange — segundo usuario con el mismo rol; env apunta a él
        pinot_store["Dim_Usuario_Rol"].append({"idusuario": 3, "idrol": 10})
        settings.SOPORTE_SUPERVISOR_USER_ID = 3
        repo = SupervisorSoporteRepository()

        # Act / Assert
        assert repo.get_supervisor_idusuario() == 3

    def test_get_supervisor_idusuario_when_varios_sin_env_elige_menor_id(
        self, mock_pinot, mock_kafka, pinot_store, settings
    ):
        # Arrange
        pinot_store["Dim_Usuario_Rol"].append({"idusuario": 3, "idrol": 10})
        settings.SOPORTE_SUPERVISOR_USER_ID = None
        repo = SupervisorSoporteRepository()

        # Act / Assert
        assert repo.get_supervisor_idusuario() == 2
