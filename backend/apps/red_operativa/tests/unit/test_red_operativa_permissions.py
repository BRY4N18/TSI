from types import SimpleNamespace

import pytest
from rest_framework.test import APIRequestFactory

from apps.red_operativa.permissions import (
    IsAdministradorOrOperador,
    IsAdministradorRedOperativa,
    IsOperadorDisponibilidadExterna,
)


@pytest.mark.unit
class TestRedOperativaPermissions:
    def test_administrador_red_operativa_when_admin_returns_true(self):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Administrador"])
        perm = IsAdministradorRedOperativa()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is True

    def test_administrador_red_operativa_when_operador_returns_false(self):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Operador"])
        perm = IsAdministradorRedOperativa()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is False

    def test_operador_disponibilidad_when_operador_returns_true(self):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Operador"])
        perm = IsOperadorDisponibilidadExterna()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is True

    def test_administrador_or_operador_when_unauthenticated_returns_false(self):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=False, roles=[])
        perm = IsAdministradorOrOperador()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is False
