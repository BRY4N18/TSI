import pytest

from core.repositories.suscripciones.factura_repository import FacturaRepository

pytestmark = pytest.mark.repository


class TestFacturaRepository:
    def test_create_numero_factura_seq(self, mock_pinot, mock_kafka):
        # Arrange
        repo = FacturaRepository()
        # Act
        fac = repo.create(
            {
                "id_cliente": 1,
                "id_suscripcion": 1,
                "idmetodopago": 1,
                "periodo": "2026-07",
                "monto_base": 49.0,
            }
        )
        # Assert
        assert fac["numero_factura"].startswith("FAC-202607-")
        assert fac["impuestos"] == 0.0
        assert fac["estado_pago"] == "Pendiente"
        assert fac["monto_total"] == 49.0
