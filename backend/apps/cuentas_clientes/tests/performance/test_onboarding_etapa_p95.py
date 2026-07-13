import pytest

from apps.cuentas_clientes.services.onboarding_service import OnboardingService


@pytest.mark.slow
@pytest.mark.service
class TestOnboardingEtapaP95:
    def test_completar_etapa_p95_under_threshold(
        self, mock_pinot, mock_kafka, mock_cuenta_pendiente_onboarding
    ):
        # Arrange
        service = OnboardingService()
        cliente_id = mock_cuenta_pendiente_onboarding
        samples_ms: list[float] = []

        # Act
        for _ in range(20):
            import time

            start = time.perf_counter()
            service.get_progreso(user_id=5, roles=["Cliente"], cliente_id=cliente_id)
            samples_ms.append((time.perf_counter() - start) * 1000)

        samples_ms.sort()
        p95 = samples_ms[int(len(samples_ms) * 0.95) - 1]

        # Assert
        assert p95 <= 300
