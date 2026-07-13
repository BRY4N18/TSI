import pytest

from core.repositories.cuentas_clientes.session_repository import SessionRepository


@pytest.mark.repository
class TestSessionRepository:
    def test_find_by_id_when_exists_returns_session(self, mock_pinot, mock_kafka):
        # Arrange
        repo = SessionRepository()

        # Act
        result = repo.find_by_id(1)

        # Assert
        assert result is not None
        assert result["idsession"] == 1
        assert result["estadosession"] == "Inicio sesion"

    def test_create_when_valid_publishes_to_kafka(self, mock_pinot, mock_kafka):
        # Arrange
        repo = SessionRepository()
        rows = repo.pinot.query("SELECT MAX(idsession) AS max_id FROM Fact_Session")
        expected_id = (rows[0].get("max_id") or 0) + 1

        # Act
        session = repo.create(
            user_id=1,
            token="new-token",
            navegador="pytest",
            refresh_token="refresh-abc",
        )

        # Assert
        assert session["idsession"] == expected_id
        assert session["estadosession"] == "Inicio sesion"
        assert len(mock_kafka) == 1

    def test_close_session_when_active_updates_status(self, mock_pinot, mock_kafka):
        # Arrange
        repo = SessionRepository()

        # Act
        result = repo.close_session(1)

        # Assert
        assert result is not None
        assert result["estadosession"] == "Cierre sesion"
        assert result["fechahoracierresesion"] is not None

    def test_is_active_when_closed_returns_false(self, mock_pinot, mock_kafka):
        # Arrange
        repo = SessionRepository()
        repo.close_session(1)

        # Act
        active = repo.is_active(1)

        # Assert
        assert active is False
