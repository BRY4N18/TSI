import pytest

from apps.ventas_crm.throttles import ProspectoRegistroThrottle


@pytest.mark.unit
def test_prospecto_registro_throttle_scope():
    # Arrange / Act
    throttle = ProspectoRegistroThrottle()
    # Assert
    assert throttle.scope == "prospecto_registro"
