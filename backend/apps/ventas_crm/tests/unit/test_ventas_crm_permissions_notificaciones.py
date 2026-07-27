from types import SimpleNamespace

import pytest

from apps.ventas_crm.permissions import IsGerenteOrAdminNotificaciones

pytestmark = pytest.mark.unit


def test_permissions_notificaciones_gerente_ok_operador_no():
    # Arrange
    perm = IsGerenteOrAdminNotificaciones()
    ok = SimpleNamespace(is_authenticated=True, roles=["GerenteVentas"])
    bad = SimpleNamespace(is_authenticated=True, roles=["Operador"])
    # Act / Assert
    assert perm.has_permission(SimpleNamespace(user=ok), None)
    assert not perm.has_permission(SimpleNamespace(user=bad), None)
