import pytest

from core.repositories.suscripciones.solicitud_cambio_plan_repository import (
    SolicitudCambioPlanRepository,
)

pytestmark = pytest.mark.repository


class TestSolicitudCambioPlanRepository:
    def test_create_pendiente(self, mock_pinot, mock_kafka):
        # Arrange
        repo = SolicitudCambioPlanRepository()
        # Act
        sol = repo.create(
            {
                "idcliente": 1,
                "idplanactual": 1,
                "idplansolicitado": 2,
                "motivo": "necesito más unidades",
            }
        )
        # Assert
        assert sol["estado"] == "Pendiente"
        assert repo.find_pendiente(1)["idsolicitud"] == sol["idsolicitud"]
