"""CA-SUSF-016 — listado planes p95 < 2s (mock Pinot; umbral local ≤100ms)."""

from __future__ import annotations

import time

import pytest

from core.repositories.suscripciones.plan_repository import PlanRepository


@pytest.mark.slow
class TestListPlanesP95:
    def test_list_planes_p95_under_100ms(self, mock_pinot, mock_kafka, pinot_store):
        for i in range(5, 55):
            pinot_store["Dim_Plan"].append(
                {
                    "idplan": i,
                    "nombre": f"Perf Plan {i}",
                    "nivel": "Básico",
                    "limites": '{"unidades_max": 1, "usuarios_max": 1, "api_calls_mes": 1, "api_calls_minuto": 1}',
                    "activo": True,
                    "precio": 10.0,
                    "fecha_actualizacion": "2026-01-01T00:00:00+00:00",
                }
            )

        repo = PlanRepository()
        samples: list[float] = []
        for _ in range(20):
            t0 = time.perf_counter()
            repo.list(activo=True, limit=20, q="Perf")
            samples.append((time.perf_counter() - t0) * 1000)
        samples.sort()
        p95 = samples[int(len(samples) * 0.95) - 1]
        assert p95 <= 100.0, f"p95={p95:.2f}ms exceeds 100ms"
