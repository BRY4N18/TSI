import pytest

from apps.ventas_crm.throttles import DemoInteraccionTokenThrottle, DemoSesionIpThrottle

pytestmark = pytest.mark.unit


def test_throttle_scopes():
    # Arrange / Act / Assert
    assert DemoSesionIpThrottle().scope == "demo_sesion_ip"
    assert DemoInteraccionTokenThrottle().scope == "demo_interaccion_token"
