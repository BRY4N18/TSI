from types import SimpleNamespace

import pytest
from rest_framework.test import APIRequestFactory

from apps.suscripciones.permissions import IsAdministradorBilling, IsProveedorCuenta

pytestmark = pytest.mark.unit


class TestSuscripcionesPermissions:
    def test_admin_permission(self, mock_pinot, mock_kafka):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(
            is_authenticated=True, idusuario=1, roles=["Administrador"]
        )
        # Act / Assert
        assert IsAdministradorBilling().has_permission(request, None)

    def test_proveedor_sets_billing_idcliente(self, mock_pinot, mock_kafka):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(
            is_authenticated=True, idusuario=3, roles=["Cliente"]
        )
        # Act
        ok = IsProveedorCuenta().has_permission(request, None)
        # Assert
        assert ok
        assert request.billing_idcliente == 1
