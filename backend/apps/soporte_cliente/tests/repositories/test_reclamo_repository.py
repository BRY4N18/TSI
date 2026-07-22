import pytest

from core.repositories.soporte.reclamo_repository import ReclamoRepository


@pytest.mark.repository
class TestReclamoRepository:
    def test_create_when_valid_publishes_and_resolves_idestadosoporte(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ReclamoRepository()

        # Act
        record = repo.create(
            {
                "idcliente": 1,
                "asunto": "API caída",
                "descripcion": "El endpoint no responde",
                "tipo": "tecnico",
                "estado": "Abierto",
            }
        )

        # Assert
        assert record["id_reclamo"] == 1
        assert record["idestadosoporte"] == 1  # Dim_Estado_Soporte "Abierto"
        assert len(mock_kafka) == 1

    def test_update_when_not_found_raises(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ReclamoRepository()

        # Act / Assert
        with pytest.raises(LookupError):
            repo.update(999, {"estado": "Cerrado"})

    def test_list_when_filtered_by_idcliente_returns_only_own(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ReclamoRepository()
        repo.create({"idcliente": 1, "asunto": "A", "descripcion": "d", "tipo": "t", "estado": "Abierto"})
        repo.create({"idcliente": 2, "asunto": "B", "descripcion": "d", "tipo": "t", "estado": "Abierto"})

        # Act
        items = repo.list(idcliente=1)

        # Assert
        assert len(items) == 1
        assert items[0]["idcliente"] == 1
