import pytest

from apps.cuentas_clientes.services.baja_cuenta_service import BajaCuentaService
from apps.cuentas_clientes.services.transferencia_propiedad_service import (
    TransferenciaPropiedadService,
)


@pytest.mark.slow
@pytest.mark.service
class TestTransferenciaP95:
    def test_transferencia_p95_under_threshold(self, mock_pinot, mock_kafka):
        # Arrange — list elegibles is read-only; transfer mutates admin_local_id
        service = TransferenciaPropiedadService()
        samples_ms: list[float] = []

        # Act
        for _ in range(20):
            import time

            start = time.perf_counter()
            service.list_usuarios_elegibles(
                user_id=3,
                roles=["Cliente"],
                cliente_id=1,
            )
            samples_ms.append((time.perf_counter() - start) * 1000)

        samples_ms.sort()
        p95 = samples_ms[int(len(samples_ms) * 0.95) - 1]

        # Assert — threshold 500ms per plan (mocks)
        assert p95 <= 500


@pytest.mark.slow
@pytest.mark.service
class TestCuentaBajaP95:
    def test_baja_p95_under_threshold(self, mock_pinot, mock_kafka):
        # Arrange
        service = BajaCuentaService()
        samples_ms: list[float] = []

        # Act
        for _ in range(20):
            import time

            start = time.perf_counter()
            service.dar_baja(
                user_id=1,
                roles=["Administrador"],
                cliente_id=1,
                motivo=None,
            )
            samples_ms.append((time.perf_counter() - start) * 1000)

        samples_ms.sort()
        p95 = samples_ms[int(len(samples_ms) * 0.95) - 1]

        # Assert — threshold 500ms per plan (mocks)
        assert p95 <= 500
