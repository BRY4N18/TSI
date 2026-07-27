import pytest

from apps.ventas_crm.demo_tokens import issue_demo_grant, verify_demo_grant

pytestmark = pytest.mark.unit


def test_demo_grant_hmac_valido_e_invalido():
    # Arrange / Act
    grant = issue_demo_grant(42)
    # Assert
    assert verify_demo_grant(grant, 42)
    assert not verify_demo_grant(grant, 43)
    assert not verify_demo_grant("bad.grant.value", 42)
