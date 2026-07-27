import pytest

from apps.suscripciones.services.alta_suscripcion_service import (
    AltaSuscripcionError,
    AltaSuscripcionService,
)
from conftest import PINOT_STORE

pytestmark = pytest.mark.service


class TestAltaSuscripcionService:
    def test_conflict_si_ya_activa(self, mock_pinot, mock_kafka):
        # Arrange / Act / Assert
        with pytest.raises(AltaSuscripcionError) as exc:
            AltaSuscripcionService().ejecutar(idcliente=1, idplan=2)
        assert exc.value.http_status == 409

    def test_alta_cliente_sin_suscripcion(self, mock_pinot, mock_kafka):
        # Arrange
        PINOT_STORE["Fact_Suscripcion"].clear()
        PINOT_STORE["Dim_Cliente"].append(
            {
                "idcliente": 99,
                "nombre": "Nuevo",
                "estado": "Activo",
                "admin_local_id": 99,
                "plan_suscripcion": None,
            }
        )
        # Act
        result = AltaSuscripcionService().ejecutar(idcliente=99, idplan=1)
        # Assert
        assert result["suscripcion"]["estado"] == "Activa"
        assert result["suscripcion"]["idcliente"] == 99
