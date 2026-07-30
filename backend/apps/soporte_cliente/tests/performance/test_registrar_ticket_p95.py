import time

import pytest

from apps.soporte_cliente.services.registrar_ticket_service import RegistrarTicketService


@pytest.mark.slow
@pytest.mark.service
class TestRegistrarTicketP95:
    def test_registrar_p95_under_3s(self, mock_pinot, mock_kafka):
        # Arrange — RNF-TIC-003: registro (clasificación + SLA) < 3s
        service = RegistrarTicketService()
        samples_ms: list[float] = []

        # Act
        for i in range(20):
            start = time.perf_counter()
            service.registrar(
                idcliente=1,
                asunto=f"Perf API timeout {i}",
                descripcion=f"error 500 constante desde hace 1 hora iter {i}",
                tipo="tecnico",
                idusuario=3,
            )
            samples_ms.append((time.perf_counter() - start) * 1000)

        samples_ms.sort()
        p95 = samples_ms[int(len(samples_ms) * 0.95) - 1]

        # Assert — umbral normativo 3000ms; con mocks locales se espera mucho menos
        assert p95 <= 3000, f"p95={p95:.1f}ms samples={samples_ms}"
