import pytest

from core.repositories.cuentas_clientes.user_repository import UserRepository


@pytest.mark.repository
class TestUserRepository:
    def test_find_by_gmail_when_exists_returns_user(self, mock_pinot, mock_kafka):
        # Arrange
        repo = UserRepository()

        # Act
        result = repo.find_by_gmail("admin@tsi.com")

        # Assert
        assert result is not None
        assert result["gmail"] == "admin@tsi.com"

    def test_create_when_valid_publishes_to_kafka(self, mock_pinot, mock_kafka):
        # Arrange
        repo = UserRepository()
        data = {
            "nombres": "Nuevo",
            "apellidos": "Usuario",
            "gmail": "nuevo@tsi.com",
            "identificacion": "1111111111",
        }

        # Act
        user = repo.create(data)

        # Assert
        assert user["idusuario"] > 2
        assert user["gmail"] == "nuevo@tsi.com"
        assert len(mock_kafka) == 1

    def test_deactivate_when_exists_sets_activo_false(self, mock_pinot, mock_kafka):
        # Arrange
        repo = UserRepository()

        # Act
        user = repo.deactivate(2)

        # Assert
        assert user is not None
        assert user["activo"] is False
