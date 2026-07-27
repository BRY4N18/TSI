import pytest

from core.repositories.soporte.suscripcion_repository import SuscripcionRepository

pytestmark = pytest.mark.repository


def test_soporte_wrapper_title_case(mock_pinot, mock_kafka):
    assert SuscripcionRepository().find_idplan_activo(1) == 1
