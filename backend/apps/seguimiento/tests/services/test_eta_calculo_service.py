import pytest

from apps.seguimiento.services.eta_calculo_service import EtaCalculoService


@pytest.mark.service
class TestEtaCalculoService:
    def test_eta_minutos_when_same_point_returns_zero(self):
        # Arrange
        svc = EtaCalculoService()

        # Act
        eta = svc.eta_minutos(19.43, -99.13, 19.43, -99.13)

        # Assert
        assert eta == 0

    def test_eta_minutos_when_far_returns_positive(self):
        # Arrange
        svc = EtaCalculoService()

        # Act
        eta = svc.eta_minutos(19.43, -99.13, 19.50, -99.20)

        # Assert
        assert eta >= 1
