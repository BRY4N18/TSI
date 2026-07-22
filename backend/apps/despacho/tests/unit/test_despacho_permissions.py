from types import SimpleNamespace

import pytest
from rest_framework.test import APIRequestFactory

from apps.despacho.permissions import (
    IsDirectorTecnologicoOrAdmin,
    IsOperadorDespacho,
    IsUnidadDespachoOwn,
)


@pytest.mark.unit
class TestDespachoPermissions:
    def test_unidad_despacho_own_when_linked_returns_true(self, mock_pinot, mock_kafka):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Unidad"], idusuario=6)
        perm = IsUnidadDespachoOwn()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is True

    def test_operador_despacho_when_operador_returns_true(self):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Operador"])
        perm = IsOperadorDespacho()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is True

    def test_director_tecnologico_when_admin_returns_true(self):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(is_authenticated=True, roles=["Administrador"])
        perm = IsDirectorTecnologicoOrAdmin()

        # Act
        result = perm.has_permission(request, None)

        # Assert
        assert result is True
