import pytest

from core.repositories.cuentas_clientes.role_repository import RoleRepository


@pytest.mark.repository
class TestRoleRepository:
    def test_get_user_roles_when_assigned_returns_role_names(self, mock_pinot, mock_kafka):
        # Arrange
        repo = RoleRepository()

        # Act
        roles = repo.get_user_roles(1)

        # Assert
        assert "Administrador" in roles

    def test_create_role_when_valid_publishes_to_kafka(self, mock_pinot, mock_kafka):
        # Arrange
        repo = RoleRepository()

        # Act
        role = repo.create_role({"rol": "Supervisor", "descripcion": "Supervisor de turno"})

        # Assert
        assert role["idrol"] > 2
        assert role["rol"] == "Supervisor"
        assert len(mock_kafka) == 1

    def test_assign_role_to_user_publishes_event(self, mock_pinot, mock_kafka):
        # Arrange
        repo = RoleRepository()

        # Act
        assignment = repo.assign_role_to_user(2, 1)

        # Assert
        assert assignment["idusuario"] == 2
        assert assignment["idrol"] == 1
        assert len(mock_kafka) == 1

    def test_assign_role_to_user_genera_clave_primaria_unica(
        self, mock_pinot, mock_kafka
    ):
        """`Dim_Usuario_Rol` es upsert por `idusuariorol`.

        El payload no llevaba esa clave, así que la fila aterrizaba con el defecto de
        Pinot para INT (`Integer.MIN_VALUE`) y cada asignación nueva **sobrescribía a
        la anterior**: solo podía existir una en todo el sistema. El usuario pisado se
        quedaba sin roles y no podía volver a entrar.
        """
        # Arrange
        repo = RoleRepository()
        # Act — dos asignaciones a usuarios distintos
        primera = repo.assign_role_to_user(101, 1)
        segunda = repo.assign_role_to_user(102, 1)
        # Assert
        for asignacion in (primera, segunda):
            assert isinstance(asignacion["idusuariorol"], int)
            assert asignacion["idusuariorol"] > 0
        assert primera["idusuariorol"] != segunda["idusuariorol"]

    def test_assign_role_to_user_es_idempotente(self, mock_pinot, mock_kafka):
        """Repetir la misma asignación no debe duplicar filas ni consumir claves."""
        # Arrange
        repo = RoleRepository()
        # Act
        primera = repo.assign_role_to_user(103, 1)
        publicados = len(mock_kafka)
        repetida = repo.assign_role_to_user(103, 1)
        # Assert
        assert repetida["idusuariorol"] == primera["idusuariorol"]
        assert len(mock_kafka) == publicados
