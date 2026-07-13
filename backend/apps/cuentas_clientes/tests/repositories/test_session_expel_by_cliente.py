import pytest

from core.repositories.cuentas_clientes.session_repository import SessionRepository


@pytest.mark.repository
class TestSessionExpelByCliente:
    def test_expel_all_by_cliente_revokes_active_sessions(self, mock_pinot, mock_kafka):
        # Arrange
        repo = SessionRepository()

        # Act
        count = repo.expel_all_by_cliente(1)

        # Assert
        assert count >= 1
        for session in repo.pinot.query(
            "SELECT * FROM Fact_Session WHERE idusuario = %(idusuario)s",
            {"idusuario": 3},
        ):
            if session["idsession"] == 3:
                assert session["estadosession"] == "Expulsado"
