import pytest


@pytest.mark.service
@pytest.mark.skip(reason="CU-O01 retirado — registro solo vía O14→O16")
class TestRegistroCuentaService:
    def test_registrar_when_valid_creates_cliente(self):
        pass
