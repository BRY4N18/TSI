import pytest

from core.repositories.despacho.despacho_repository import DespachoRepository


@pytest.mark.repository
class TestDespachoRepository:
    def test_publish_create_when_valid_publishes_and_reads_back(self, mock_pinot, mock_kafka):
        # Arrange
        repo = DespachoRepository()

        # Act
        created = repo.publish_create(
            {
                "idaccidente": "ACC-DES-1",
                "idunidademergencia": 1,
                "idnotificaciondespacho": 1,
                "idorigendespacho": 1,
            }
        )
        found = repo.find_by_id(created["iddespacho"])

        # Assert
        assert found is not None
        assert found["idaccidente"] == "ACC-DES-1"
        assert found["activo"] is True
        assert len(mock_kafka) == 1

    def test_publish_update_activo_when_exists_deactivates(self, mock_pinot, mock_kafka):
        # Arrange
        repo = DespachoRepository()
        created = repo.publish_create(
            {
                "idaccidente": "ACC-DES-2",
                "idunidademergencia": 1,
                "idnotificaciondespacho": 2,
                "idorigendespacho": 1,
            }
        )

        # Act
        updated = repo.publish_update(created["iddespacho"], {"activo": False})
        found = repo.find_by_id(created["iddespacho"])

        # Assert
        assert updated is not None
        assert found["activo"] is False
        assert len(mock_kafka) == 2
