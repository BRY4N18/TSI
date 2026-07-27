import pytest

from apps.suscripciones.services.pasarela.simulador_pasarela import SimuladorPasarela

pytestmark = pytest.mark.unit


class TestSimuladorPasarela:
    def test_cobrar_exitoso_por_defecto(self):
        # Arrange
        sim = SimuladorPasarela()
        # Act
        result = sim.cobrar(monto=10.0, tokenpasarela="tok", idempotency_key="k1")
        # Assert
        assert result.exitoso is True
        assert result.codigo == "Exitoso"

    def test_force_fail(self):
        # Arrange / Act
        result = SimuladorPasarela().cobrar(
            monto=10.0, tokenpasarela="tok", idempotency_key="k2", force_fail=True
        )
        # Assert
        assert result.exitoso is False
