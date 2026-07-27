"""T060 — cancelación tests (also in test_cambio_plan_service for convenience)."""

import pytest

from apps.suscripciones.services.cancelacion_service import CancelacionError, CancelacionService

pytestmark = pytest.mark.service


class TestCancelacionServiceDedicated:
    def test_motivo_requerido(self, mock_pinot, mock_kafka):
        with pytest.raises(CancelacionError):
            CancelacionService().cancelar(idcliente=1, motivocancelacion="")
