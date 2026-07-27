from types import SimpleNamespace

import pytest
from rest_framework.test import APIRequestFactory

from apps.red_operativa.permissions import IsProveedorFlota


@pytest.mark.unit
class TestRedOperativaPermissionsProveedor:
    def test_proveedor_flota_when_cliente_activo_returns_true(self, mock_pinot, mock_kafka):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=True, idusuario=3, roles=["Cliente"])
        perm = IsProveedorFlota()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is True
        assert request.proveedor_idcliente == 1

    def test_proveedor_flota_when_admin_returns_false(self, mock_pinot, mock_kafka):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=True, idusuario=1, roles=["Administrador"])
        perm = IsProveedorFlota()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is False

    def test_proveedor_flota_when_cliente_no_activo_returns_false(self, mock_pinot, mock_kafka, pinot_store):
        # Arrange
        pinot_store["Dim_Cliente"][0]["estado"] = "Pendiente"
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=True, idusuario=3, roles=["Cliente"])
        perm = IsProveedorFlota()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is False
