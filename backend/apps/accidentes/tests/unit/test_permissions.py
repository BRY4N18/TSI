from types import SimpleNamespace

import pytest
from rest_framework.test import APIRequestFactory

from apps.accidentes.permissions import (
    AccidentesLecturaPermission,
    OperadorEmergenciasPermission,
    UnidadEmergenciaPermission,
)


@pytest.mark.unit
class TestAccidentePermissions:
    def test_operador_permission_when_operador_returns_true(self):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Operador"])
        perm = OperadorEmergenciasPermission()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is True

    def test_operador_permission_when_unidad_returns_false(self):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Unidad"])
        perm = OperadorEmergenciasPermission()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is False

    def test_unidad_permission_when_unidad_returns_true(self):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Unidad"])
        perm = UnidadEmergenciaPermission()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is True

    @pytest.mark.parametrize("rol", ["Operador", "Tecnico", "Administrador"])
    def test_lectura_permission_when_authorized_role_returns_true(self, rol):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=[rol])
        perm = AccidentesLecturaPermission()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is True

    def test_lectura_permission_when_unidad_returns_false(self):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Unidad"])
        perm = AccidentesLecturaPermission()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is False

    def test_lectura_permission_when_unauthenticated_returns_false(self):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=False, roles=[])
        perm = AccidentesLecturaPermission()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is False
