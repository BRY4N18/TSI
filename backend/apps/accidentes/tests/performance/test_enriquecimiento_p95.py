import time

import pytest


@pytest.mark.slow
@pytest.mark.api
class TestEnriquecimientoP95:
    def test_catalogos_p95_under_2s(self, api_client, tecnico_auth_headers):
        # Arrange
        latencies = []

        # Act
        for _ in range(5):
            start = time.perf_counter()
            response = api_client.get(
                "/api/v1/catalogos/periodos-dias", **tecnico_auth_headers
            )
            latencies.append(time.perf_counter() - start)
            assert response.status_code == 200

        # Assert
        p95 = sorted(latencies)[int(len(latencies) * 0.95) - 1]
        assert p95 <= 2.0

    def test_alta_conductor_p95_under_3s(
        self, api_client, tecnico_auth_headers, accidente_activo
    ):
        # Arrange
        latencies = []

        # Act
        for i in range(5):
            start = time.perf_counter()
            response = api_client.post(
                f"/api/v1/accidentes/{accidente_activo}/enriquecimiento/conductores",
                {
                    "conductor": {
                        "identificacion": f"100000000{i}",
                        "nombres": "Perf",
                        "apellidos": "Test",
                    },
                    "idestadoconductor": 1,
                    "vehiculo": {"tipovehiculo": "Auto"},
                },
                format="json",
                **tecnico_auth_headers,
            )
            latencies.append(time.perf_counter() - start)
            assert response.status_code == 201

        # Assert
        p95 = sorted(latencies)[int(len(latencies) * 0.95) - 1]
        assert p95 <= 3.0
