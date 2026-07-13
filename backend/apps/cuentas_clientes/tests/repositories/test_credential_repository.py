import pytest

from core.repositories.cuentas_clientes.credential_repository import CredentialRepository


@pytest.mark.repository
class TestCredentialRepository:
    def test_verify_password_when_correct_returns_true(self, mock_pinot, mock_kafka):
        # Arrange
        repo = CredentialRepository()
        cred = repo.find_by_user_id(1)

        # Act
        valid = repo.verify_password("password123", cred["contrasena"])

        # Assert
        assert valid is True

    def test_verify_password_when_wrong_returns_false(self, mock_pinot, mock_kafka):
        # Arrange
        repo = CredentialRepository()
        cred = repo.find_by_user_id(1)

        # Act
        valid = repo.verify_password("wrongpassword", cred["contrasena"])

        # Assert
        assert valid is False

    def test_reset_password_when_exists_updates_status(self, mock_pinot, mock_kafka):
        # Arrange
        repo = CredentialRepository()

        # Act
        result = repo.reset_password(1, "tempPass1234")

        # Assert
        assert result is not None
        assert result["estadocredencial"] == "Cambio contraseña"
        assert len(mock_kafka) == 1
