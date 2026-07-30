from types import SimpleNamespace

import pytest
from rest_framework.test import APIRequestFactory

from apps.red_operativa.permissions import IsAdministradorRedOperativa


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

    def test_administrador_red_operativa_when_unauthenticated_returns_false(self):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=False, roles=[])
        perm = IsAdministradorRedOperativa()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is False
