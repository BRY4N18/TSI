import pytest

from apps.suscripciones.jobs.renovacion_job import run_renovacion
from conftest import PINOT_STORE

pytestmark = pytest.mark.service


def test_renovacion_job_noop(mock_pinot, mock_kafka):
    PINOT_STORE["Fact_Suscripcion"][0]["fecha_fin"] = 4102444800000
    assert run_renovacion()["renovadas"] == 0
