import pytest

from apps.suscripciones.throttles import AdminBillingThrottle, ProveedorBillingWriteThrottle

pytestmark = pytest.mark.unit


class TestSuscripcionesThrottles:
    def test_rates(self):
        # Arrange / Act / Assert
        assert ProveedorBillingWriteThrottle().rate == "60/min"
        assert AdminBillingThrottle().rate == "100/min"
