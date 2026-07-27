import pytest

from core.repositories.suscripciones.metodo_pago_repository import MetodoPagoRepository

pytestmark = pytest.mark.repository


class TestMetodoPagoRepository:
    def test_create_and_find_activo(self, mock_pinot, mock_kafka):
        # Arrange
        repo = MetodoPagoRepository()
        # Act
        created = repo.create(
            {
                "idcliente": 1,
                "tipo": "tarjeta",
                "tokenpasarela": "tok_x",
                "ultimosdigitos": "4242",
            }
        )
        # Assert
        assert created["activo"] is True
        assert repo.find_activo(1)["idmetodopago"] == created["idmetodopago"]
        assert "4242" in created["ultimosdigitos"]
