import pytest
from rest_framework.test import APIRequestFactory
from types import SimpleNamespace

from apps.seguimiento.permissions import (
    IsClienteExpediente,
    IsOperadorSeguimiento,
    IsUnidadSeguimiento,
)


@pytest.mark.unit
class TestSeguimientoPermissions:
    def test_unidad_seguimiento_when_linked_returns_true(self, mock_pinot, mock_kafka):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Unidad"], idusuario=6)
        perm = IsUnidadSeguimiento()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is True

    def test_operador_seguimiento_when_operador_returns_true(self):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Operador"])
        perm = IsOperadorSeguimiento()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is True

    def test_cliente_expediente_when_cliente_returns_true(self):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Cliente"])
        perm = IsClienteExpediente()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is True
