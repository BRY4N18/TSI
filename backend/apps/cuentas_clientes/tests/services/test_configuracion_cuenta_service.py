import pytest


@pytest.mark.service
@pytest.mark.skip(reason="CU-O12 retirado — logo cliente; plan → Suscripciones")
class TestConfiguracionCuentaService:
    def test_configurar_when_valid_sets_pendiente(self):
        pass
