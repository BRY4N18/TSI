"""T059 renovacion dedicated file."""

import pytest

from apps.suscripciones.services.renovacion_service import RenovacionService
from conftest import PINOT_STORE

pytestmark = pytest.mark.service


class TestRenovacionServiceDedicated:
    def test_no_renueva_si_fecha_futura(self, mock_pinot, mock_kafka):
        PINOT_STORE["Fact_Suscripcion"][0]["fecha_fin"] = 4102444800000  # far future
        assert RenovacionService().ejecutar_batch() == []
