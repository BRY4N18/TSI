import pytest

from core.repositories.evidencia.nota_campo_repository import NotaCampoRepository


@pytest.mark.repository
class TestNotaCampoRepository:
    def test_create_campo_when_valid_publishes_and_reads_back(self, mock_pinot, mock_kafka):
        # Arrange
        repo = NotaCampoRepository()

        # Act
        created = repo.create_campo(
            idaccidente="ACC-1",
            idusuario=7,
            nota="Testigo reporta daños",
            tipo="Declaración de testigo",
            fechahora=1_700_000_000_000,
        )
        rows = repo.list_by_accidente("ACC-1")

        # Assert
        assert created["tipo"] == "Declaración de testigo"
        assert len(rows) == 1
        assert rows[0]["sincronizado"] is True

    def test_create_campo_when_invalid_tipo_raises(self, mock_pinot, mock_kafka):
        # Arrange
        repo = NotaCampoRepository()

        # Act / Assert
        with pytest.raises(ValueError):
            repo.create_campo(
                idaccidente="ACC-1",
                idusuario=7,
                nota="x",
                tipo="escalamiento",
                fechahora=1,
            )
