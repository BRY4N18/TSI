import pytest

from core.repositories.evidencia.implicado_repository import (
    PAYLOAD_KEYS,
    ImplicadoRepository,
)


@pytest.mark.repository
class TestImplicadoRepository:
    def test_create_when_valid_publishes_and_lists_by_accidente(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        repo = ImplicadoRepository()

        # Act
        created = repo.create(
            idaccidente="ACC-1",
            tipoimplicado="Peaton",
            estadoimplicado="Lesionado",
            genero="M",
            edad=40,
        )
        listed = repo.list_activos_by_accidente("ACC-1")

        # Assert
        assert created["idimplicado"] == listed[0]["idimplicado"]
        assert listed[0]["tipoimplicado"] == "Peaton"
        assert listed[0]["estadoimplicado"] == "Lesionado"
        assert set(created.keys()) == PAYLOAD_KEYS
        assert "identificacion" not in created
        assert len(mock_kafka) == 1

    def test_soft_delete_when_exists_sets_activo_false(self, mock_pinot, mock_kafka):
        # Arrange
        repo = ImplicadoRepository()
        created = repo.create(
            idaccidente="ACC-1",
            tipoimplicado="Testigo",
            estadoimplicado="Desconocido",
        )

        # Act
        deleted = repo.soft_delete(idimplicado=created["idimplicado"])

        # Assert
        assert deleted is not None
        assert deleted["activo"] is False
        assert set(deleted.keys()) <= PAYLOAD_KEYS
        assert repo.list_activos_by_accidente("ACC-1") == []
