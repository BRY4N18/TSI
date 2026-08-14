import pytest

from core.pinot.tiempo import SIN_FECHA
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

    def test_expiracion_se_publica_como_epoch_no_como_texto(self, mock_pinot, mock_kafka):
        """`fechaexpiracion` es LONG en el esquema: `MM/AA` hacía que Pinot
        descartara la fila entera y el método de pago no llegaba a existir."""
        # Arrange
        repo = MetodoPagoRepository()
        # Act
        repo.create(
            {
                "idcliente": 1,
                "tipo": "tarjeta",
                "tokenpasarela": "tok_x",
                "ultimosdigitos": "4242",
                "fechaexpiracion": "12/30",
            }
        )
        # Assert
        publicado = mock_kafka[-1]["payload"]["fechaexpiracion"]
        assert isinstance(publicado, int)
        # Último milisegundo de diciembre de 2030
        assert publicado == 1924991999999

    @pytest.mark.parametrize("valor", [None, "", "sin-fecha", "13/30"])
    def test_expiracion_invalida_usa_centinela(self, valor, mock_pinot, mock_kafka):
        """Nunca se propaga texto a la columna: lo ilegible cae en SIN_FECHA."""
        # Arrange
        repo = MetodoPagoRepository()
        # Act
        repo.create(
            {
                "idcliente": 1,
                "tipo": "transferencia",
                "tokenpasarela": "tok_y",
                "ultimosdigitos": "0000",
                "fechaexpiracion": valor,
            }
        )
        # Assert
        assert mock_kafka[-1]["payload"]["fechaexpiracion"] == SIN_FECHA
