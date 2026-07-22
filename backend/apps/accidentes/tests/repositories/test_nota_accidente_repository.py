import pytest

from core.repositories.accidentes.nota_accidente_repository import (
    NotaAccidenteRepository,
)


@pytest.mark.repository
class TestNotaAccidenteRepository:
    def test_create_escalamiento_when_called_publishes(self, mock_kafka):
        # Arrange
        repo = NotaAccidenteRepository()

        # Act
        result = repo.create_escalamiento(
            idaccidente="ACC-1",
            idusuario=6,
            nota="Severidad aumentada en sitio",
        )

        # Assert
        assert result["tipo"] == "escalamiento"
        assert len(mock_kafka) == 1
