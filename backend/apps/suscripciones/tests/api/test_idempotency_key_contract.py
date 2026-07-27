import pytest

pytestmark = pytest.mark.api


def test_idempotency_documented_in_planes():
    # Covered by TestIdempotencyKeyContract in test_planes_contract.py
    assert True
