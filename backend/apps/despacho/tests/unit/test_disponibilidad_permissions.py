from types import SimpleNamespace

import pytest
from rest_framework.test import APIRequestFactory

from apps.despacho.permissions import (
    IsAdministradorOrDespachoService,
    IsUnidadEmergenciaOwn,
    IsUnidadEmergenciaSelfOrAdmin,
)


@pytest.mark.unit
class TestDisponibilidadPermissions:
    def test_flota_permission_when_despacho_returns_true(self):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Despacho"])
        perm = IsAdministradorOrDespachoService()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is True

    def test_flota_permission_when_tecnico_returns_false(self):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Tecnico"])
        perm = IsAdministradorOrDespachoService()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is False

    def test_unidad_own_permission_when_unidad_with_unit_returns_true(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Unidad"], idusuario=6)
        perm = IsUnidadEmergenciaOwn()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is True

    def test_self_or_admin_when_unidad_other_unit_returns_false(
        self, mock_pinot, mock_kafka
    ):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Unidad"], idusuario=6)
        view = SimpleNamespace(kwargs={"idunidademergencia": 2})
        perm = IsUnidadEmergenciaSelfOrAdmin()

        # Act
        result = perm.has_permission(request, view)

        # Assert
        assert result is False

    def test_self_or_admin_when_admin_returns_true(self, mock_pinot, mock_kafka):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(
            is_authenticated=True, roles=["Administrador"], idusuario=1
        )
        view = SimpleNamespace(kwargs={"idunidademergencia": 2})
        perm = IsUnidadEmergenciaSelfOrAdmin()

        # Act
        result = perm.has_permission(request, view)

        # Assert
        assert result is True
