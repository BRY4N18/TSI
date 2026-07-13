import pytest

from apps.cuentas_clientes.services.cuenta_perfil_service import CuentaPerfilService


@pytest.mark.slow
@pytest.mark.service
class TestCuentaPerfilP95:
    def test_get_perfil_p95_under_threshold(self, mock_pinot, mock_kafka):
        # Arrange
        service = CuentaPerfilService()
        samples_ms: list[float] = []

        # Act
        for _ in range(20):
            import time

            start = time.perf_counter()
            service.get_perfil(user_id=3, roles=["Cliente"], cliente_id=1)
            samples_ms.append((time.perf_counter() - start) * 1000)

        samples_ms.sort()
        p95 = samples_ms[int(len(samples_ms) * 0.95) - 1]

        # Assert — threshold 300ms per plan (mocks)
        assert p95 <= 300
