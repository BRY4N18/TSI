import pytest

from core.repositories.accidentes.estado_accidente_repository import EstadoAccidenteRepository


@pytest.mark.repository
class TestEstadoAccidenteRepository:
    def test_append_estado_when_called_returns_current(self, mock_pinot, mock_kafka):
        # Arrange
        repo = EstadoAccidenteRepository()

        # Act
        repo.append_estado(idaccidente="ACC-1", estado="BORRADOR", idusuario=2)
        repo.append_estado(idaccidente="ACC-1", estado="REPORTADO", idusuario=2)
        current = repo.get_current_estado("ACC-1")
        history = repo.get_history("ACC-1")

        # Assert
        assert current == "REPORTADO"
        assert len(history) == 2
        assert len(mock_kafka) == 2
