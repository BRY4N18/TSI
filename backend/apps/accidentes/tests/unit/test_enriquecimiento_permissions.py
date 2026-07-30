from types import SimpleNamespace

import pytest
from rest_framework.test import APIRequestFactory

from apps.accidentes.permissions import (
    IsTecnicoCampoOrUnidad,
    IsTecnicoCampoOrUnidadOrAdmin,
)


@pytest.mark.unit
class TestEnriquecimientoPermissions:
    def test_write_when_admin_returns_false(self):
        # Arrange
        request = APIRequestFactory().put("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Administrador"])

        # Act / Assert
        assert IsTecnicoCampoOrUnidad().has_permission(request, None) is False

    def test_read_when_admin_returns_true(self):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Administrador"])

        # Act / Assert
        assert IsTecnicoCampoOrUnidadOrAdmin().has_permission(request, None) is True

    def test_write_when_tecnico_returns_true(self):
        # Arrange
        request = APIRequestFactory().post("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Tecnico"])

        # Act / Assert
        assert IsTecnicoCampoOrUnidad().has_permission(request, None) is True
