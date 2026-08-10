"""T059 renovacion dedicated file."""

import pytest

from apps.suscripciones.services.renovacion_service import RenovacionService
from conftest import PINOT_STORE

pytestmark = pytest.mark.service


class TestRenovacionServiceDedicated:
    def test_no_renueva_si_fecha_futura(self, mock_pinot, mock_kafka):
        PINOT_STORE["Fact_Suscripcion"][0]["fecha_fin"] = 4102444800000  # far future
        assert RenovacionService().ejecutar_batch() == []

    def test_renovacion_anual_avanza_un_ano_no_un_mes(self, mock_pinot, mock_kafka):
        # Arrange: suscripcion Anual vencida hoy -> elegible para renovar.
        sus = PINOT_STORE["Fact_Suscripcion"][0]
        sus["periodicidad"] = "Anual"
        sus["fecha_fin"] = 1704067200000  # pasado
        fecha_fin_anterior = sus["fecha_fin"]

        # Act
        resultados = RenovacionService().ejecutar_batch()

        # Assert: ~1 año de diferencia, no ~1 mes.
        assert len(resultados) == 1
        diff_dias = (resultados[0]["fecha_fin"] - fecha_fin_anterior) / 86_400_000
        assert 360 <= diff_dias <= 366
