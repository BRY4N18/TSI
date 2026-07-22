from types import SimpleNamespace

import pytest

from apps.soporte_cliente.permissions import (
    IsAdministradorSLA,
    IsClienteSoporte,
    IsNivelEscaladoSoporte,
    IsSoporteAgente,
)


def _user(roles):
    return SimpleNamespace(is_authenticated=True, roles=roles, idusuario=1)


@pytest.mark.unit
class TestSoportePermissions:
    def test_is_cliente_soporte_when_role_matches_allows(self):
        # Arrange
        request = SimpleNamespace(user=_user(["Cliente"]))

        # Act
        allowed = IsClienteSoporte().has_permission(request, None)

        # Assert
        assert allowed is True

    def test_is_soporte_agente_when_role_missing_denies(self):
        # Arrange
        request = SimpleNamespace(user=_user(["Cliente"]))

        # Act
        allowed = IsSoporteAgente().has_permission(request, None)

        # Assert
        assert allowed is False

    def test_is_nivel_escalado_soporte_when_desarrollador_apis_allows(self):
        # Arrange
        request = SimpleNamespace(user=_user(["DesarrolladorAPIs"]))

        # Act
        allowed = IsNivelEscaladoSoporte().has_permission(request, None)

        # Assert
        assert allowed is True

    def test_is_administrador_sla_when_unauthenticated_denies(self):
        # Arrange
        request = SimpleNamespace(user=SimpleNamespace(is_authenticated=False, roles=[]))

        # Act
        allowed = IsAdministradorSLA().has_permission(request, None)

        # Assert
        assert allowed is False
