"""Performance test for login endpoint — p95 <= 500ms (RNF-AUT-004)."""

import time

import pytest


@pytest.mark.slow
@pytest.mark.api
class TestLoginP95:
    P95_THRESHOLD_MS = 500
    SAMPLE_SIZE = 20

    def test_login_p95_under_threshold(self, api_client):
        # Arrange
        payload = {"gmail": "admin@tsi.com", "password": "password123"}
        durations_ms: list[float] = []

        # Act
        for _ in range(self.SAMPLE_SIZE):
            start = time.perf_counter()
            response = api_client.post("/api/v1/auth/login", payload, format="json")
            elapsed_ms = (time.perf_counter() - start) * 1000
            durations_ms.append(elapsed_ms)
            assert response.status_code == 200

        durations_ms.sort()
        p95_index = int(len(durations_ms) * 0.95) - 1
        p95_ms = durations_ms[max(p95_index, 0)]

        # Assert
        assert p95_ms <= self.P95_THRESHOLD_MS, (
            f"Login p95 {p95_ms:.1f}ms exceeds threshold {self.P95_THRESHOLD_MS}ms"
        )
