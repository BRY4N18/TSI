from types import SimpleNamespace

import pytest
from rest_framework.test import APIRequestFactory

from apps.accidentes.permissions import (
    IsTecnicoCampoOrUnidad,
    IsTecnicoCampoOrUnidadOrAdmin,
)


@pytest.mark.unit
class TestEvidenciaPermissions:
    def test_gallery_permission_when_tecnico_returns_true(self):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Tecnico"])
        perm = IsTecnicoCampoOrUnidadOrAdmin()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is True

    def test_gallery_permission_when_operador_returns_true(self):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Operador"])
        perm = IsTecnicoCampoOrUnidadOrAdmin()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is True

    def test_gallery_permission_when_admin_returns_true(self):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Administrador"])
        perm = IsTecnicoCampoOrUnidadOrAdmin()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is True

    def test_gallery_permission_when_cliente_returns_false(self):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Cliente"])
        perm = IsTecnicoCampoOrUnidadOrAdmin()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is False

    def test_capture_permission_when_admin_returns_false(self):
        # Arrange
        request = APIRequestFactory().post("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Administrador"])
        perm = IsTecnicoCampoOrUnidad()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is False

    def test_capture_permission_when_unidad_returns_true(self):
        # Arrange
        request = APIRequestFactory().post("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Unidad"])
        perm = IsTecnicoCampoOrUnidad()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is True
