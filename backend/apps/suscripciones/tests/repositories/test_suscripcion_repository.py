import pytest

from core.repositories.suscripciones.suscripcion_repository import SuscripcionRepository

pytestmark = pytest.mark.repository


class TestSuscripcionRepository:
    def test_find_activa_title_case(self, mock_pinot, mock_kafka):
        # Arrange / Act
        sus = SuscripcionRepository().find_activa_by_cliente(1)
        # Assert
        assert sus is not None
        assert sus["estado"] == "Activa"
        assert "fecha_fin" in sus

    def test_create_sets_activa_and_fecha_fin(self, mock_pinot, mock_kafka):
        # Arrange — clear seed conflict for client 2
        from conftest import PINOT_STORE

        PINOT_STORE["Fact_Suscripcion"].clear()
        repo = SuscripcionRepository()
        # Act
        created = repo.create(
            {"idcliente": 2, "idplan": 2, "precio": 149.0, "renovacionautomatica": True}
        )
        # Assert
        assert created["estado"] == "Activa"
        assert created["activo"] is True
        assert created["fecha_fin"] > created["fecha_inicio"]
