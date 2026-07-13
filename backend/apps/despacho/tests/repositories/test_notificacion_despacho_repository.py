import pytest

from core.repositories.despacho.notificacion_despacho_repository import (
    ESTADO_NOTIFICADA,
    ESTADO_PENDIENTE,
    NotificacionDespachoRepository,
)


@pytest.mark.repository
class TestNotificacionDespachoRepository:
    def test_publish_create_when_valid_defaults_to_pendiente(self, mock_pinot, mock_kafka):
        # Arrange
        repo = NotificacionDespachoRepository()

        # Act
        created = repo.publish_create(
            {
                "idaccidente": "ACC-NOT-1",
                "idunidaddemergencia": 1,
            }
        )
        found = repo.find_by_id(created["idnotificaciondespacho"])

        # Assert
        assert found is not None
        assert found["estadonotificaciondespacho"] == ESTADO_PENDIENTE
        assert len(mock_kafka) == 1

    def test_publish_update_when_called_changes_estado(self, mock_pinot, mock_kafka):
        # Arrange
        repo = NotificacionDespachoRepository()
        created = repo.publish_create(
            {
                "idaccidente": "ACC-NOT-2",
                "idunidaddemergencia": 1,
            }
        )

        # Act
        updated = repo.publish_update(
            created["idnotificaciondespacho"],
            {"estadonotificaciondespacho": ESTADO_NOTIFICADA},
        )

        # Assert
        assert updated["estadonotificaciondespacho"] == ESTADO_NOTIFICADA
        assert len(mock_kafka) == 2
