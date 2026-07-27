"""T069 consulta factura."""

import pytest

from apps.suscripciones.services.consulta_factura_service import ConsultaFacturaService

pytestmark = pytest.mark.service


class TestConsultaFacturaServiceDedicated:
    def test_detalle_ajeno_none(self, mock_pinot, mock_kafka):
        assert ConsultaFacturaService().detalle(1, "no-existe") is None
