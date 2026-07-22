import pytest

from core.repositories.soporte.historial_ticket_repository import HistorialTicketRepository


@pytest.mark.repository
class TestHistorialTicketRepository:
    def test_append_when_valid_publishes(self, mock_pinot, mock_kafka):
        # Arrange
        repo = HistorialTicketRepository()

        # Act
        record = repo.append(id_reclamo=1, tipo_accion="creacion", idusuario=1)

        # Assert
        assert record["id_historial"] == 1
        assert len(mock_kafka) == 1

    def test_repository_has_no_update_or_delete_methods(self, mock_pinot, mock_kafka):
        # Arrange / Act / Assert — RNF-TIC-002 (insert-only)
        assert not hasattr(HistorialTicketRepository, "update")
        assert not hasattr(HistorialTicketRepository, "delete")

    def test_list_by_ticket_when_multiple_returns_sorted_by_fecha(self, mock_pinot, mock_kafka):
        # Arrange
        repo = HistorialTicketRepository()
        repo.append(id_reclamo=1, tipo_accion="creacion", idusuario=1)
        repo.append(id_reclamo=1, tipo_accion="comentario", idusuario=1)

        # Act
        items = repo.list_by_ticket(1)

        # Assert
        assert len(items) == 2
        assert items[0]["tipo_accion"] == "creacion"
