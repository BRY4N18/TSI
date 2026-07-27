import pytest

from apps.suscripciones.jobs.mantenimiento_activo_job import run_mantenimiento_activo

pytestmark = pytest.mark.service


def test_mantenimiento_noop_activa(mock_pinot, mock_kafka):
    assert run_mantenimiento_activo()["desactivadas"] == 0
