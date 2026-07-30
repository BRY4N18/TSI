from types import SimpleNamespace

import pytest
from rest_framework.test import APIRequestFactory

from apps.suscripciones.permissions import (
    IsAdministradorBilling,
    IsCatalogoPlanesReader,
    IsDirectorEstrategiaBilling,
    IsProveedorCuenta,
)

pytestmark = pytest.mark.unit


class TestSuscripcionesPermissions:
    def test_admin_permission(self, mock_pinot, mock_kafka):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(
            is_authenticated=True, idusuario=1, roles=["Administrador"]
        )
        # Act / Assert
        assert IsAdministradorBilling().has_permission(request, None)

    def test_director_estrategia_permission(self, mock_pinot, mock_kafka):
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(
            is_authenticated=True, idusuario=12, roles=["DirectorEstrategia"]
        )
        assert IsDirectorEstrategiaBilling().has_permission(request, None)
        assert not IsAdministradorBilling().has_permission(request, None)

    def test_admin_cannot_mutate_as_director(self, mock_pinot, mock_kafka):
        request = APIRequestFactory().post("/")
        request.user = SimpleNamespace(
            is_authenticated=True, idusuario=1, roles=["Administrador"]
        )
        assert not IsDirectorEstrategiaBilling().has_permission(request, None)

    def test_catalogo_reader_allows_director_admin_proveedor(
        self, mock_pinot, mock_kafka
    ):
        factory = APIRequestFactory()
        for roles, uid in (
            (["DirectorEstrategia"], 12),
            (["Administrador"], 1),
            (["Cliente"], 3),
        ):
            request = factory.get("/")
            request.user = SimpleNamespace(
                is_authenticated=True, idusuario=uid, roles=roles
            )
            assert IsCatalogoPlanesReader().has_permission(request, None)

    def test_proveedor_sets_billing_idcliente(self, mock_pinot, mock_kafka):
        # Arrange
        request = APIRequestFactory().get("/")
        request.user = SimpleNamespace(
            is_authenticated=True, idusuario=3, roles=["Cliente"]
        )
        # Act
        ok = IsProveedorCuenta().has_permission(request, None)
        # Assert
        assert ok
        assert request.billing_idcliente == 1
