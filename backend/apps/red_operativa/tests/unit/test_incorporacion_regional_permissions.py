from types import SimpleNamespace

import pytest
from rest_framework.test import APIRequestFactory

from apps.red_operativa.permissions import (
    IsAdministradorOrDirectorTecnologico,
    IsDirectorTecnologico,
)


@pytest.mark.unit
class TestIncorporacionRegionalPermissions:
    def test_director_tecnologico_when_director_returns_true(self):
        # Arrange
        request = APIRequestFactory().post("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["DirectorTecnologico"])
        perm = IsDirectorTecnologico()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is True

    def test_director_tecnologico_when_administrador_returns_false(self):
        # Arrange
        request = APIRequestFactory().post("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Administrador"])
        perm = IsDirectorTecnologico()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is False

    def test_administrador_or_director_when_administrador_returns_true(self):
        # Arrange
        request = APIRequestFactory().post("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Administrador"])
        perm = IsAdministradorOrDirectorTecnologico()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is True

    def test_administrador_or_director_when_director_returns_true(self):
        # Arrange
        request = APIRequestFactory().post("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["DirectorTecnologico"])
        perm = IsAdministradorOrDirectorTecnologico()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is True

    def test_administrador_or_director_when_operador_returns_false(self):
        # Arrange
        request = APIRequestFactory().post("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Operador"])
        perm = IsAdministradorOrDirectorTecnologico()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is False

    def test_administrador_or_director_when_unauthenticated_returns_false(self):
        # Arrange
        request = APIRequestFactory().post("/")
        request.user = SimpleNamespace(is_authenticated=False, roles=[])
        perm = IsAdministradorOrDirectorTecnologico()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is False
