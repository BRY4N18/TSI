import pytest
from django.core.exceptions import ImproperlyConfigured

from apps.ventas_crm.demo_tokens import issue_demo_grant, verify_demo_grant

pytestmark = pytest.mark.unit


def test_demo_grant_hmac_valido_e_invalido():
    # Arrange / Act
    grant = issue_demo_grant(42)
    # Assert
    assert verify_demo_grant(grant, 42)
    assert not verify_demo_grant(grant, 43)
    assert not verify_demo_grant("bad.grant.value", 42)


def test_demo_grant_rechaza_secreto_default_fuera_de_debug(monkeypatch):
    # Arrange: simula despliegue con DJANGO_DEBUG=false y el secreto por
    # defecto sin configurar (el escenario inseguro que este guard evita).
    monkeypatch.setenv("DJANGO_DEBUG", "false")
    # Act / Assert
    with pytest.raises(ImproperlyConfigured):
        issue_demo_grant(1)
