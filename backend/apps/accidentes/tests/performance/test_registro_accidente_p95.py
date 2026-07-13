import time

import pytest

from apps.accidentes.services.registro_accidente_service import RegistroAccidenteService


@pytest.mark.slow
@pytest.mark.service
class TestRegistroAccidenteP95:
    def test_registrar_p95_under_threshold(self, mock_pinot, mock_kafka, accidente_payload):
        # Arrange
        service = RegistroAccidenteService()
        samples_ms: list[float] = []
        base_ts = int(time.time() * 1000) - 60_000

        # Act
        for i in range(20):
            payload = {
                **accidente_payload,
                "descripcion": f"Perf {i}",
                "latitudinicio": accidente_payload["latitudinicio"] + (i * 0.01),
                "longitudinicio": accidente_payload["longitudinicio"] + (i * 0.01),
                "fechahoraaccidente": base_ts - (i * 1000),
            }
            start = time.perf_counter()
            service.registrar(payload, idusuario=2)
            samples_ms.append((time.perf_counter() - start) * 1000)

        samples_ms.sort()
        p95 = samples_ms[int(len(samples_ms) * 0.95) - 1]

        # Assert
        assert p95 <= 500
