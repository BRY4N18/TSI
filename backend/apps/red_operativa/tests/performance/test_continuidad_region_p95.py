"""RNF-REGON-002 — continuidad de casos activos ≤100ms p95 (consulta Pinot)."""

from __future__ import annotations

import time

import pytest

from core.repositories.red_operativa.accidente_activo_read_repository import (
    AccidenteActivoReadRepository,
)
from core.repositories.red_operativa.cobertura_region_read_repository import (
    CoberturaRegionReadRepository,
)


@pytest.mark.slow
class TestContinuidadRegionP95:
    def test_existen_casos_activos_p95_under_100ms(self, mock_pinot, mock_kafka):
        repo = AccidenteActivoReadRepository()
        samples: list[float] = []
        for _ in range(20):
            t0 = time.perf_counter()
            repo.existen_casos_activos(1)
            samples.append((time.perf_counter() - t0) * 1000)
        samples.sort()
        p95 = samples[int(len(samples) * 0.95) - 1]
        assert p95 <= 100.0, f"p95={p95:.2f}ms exceeds 100ms"

    def test_count_unidades_activas_p95_under_100ms(self, mock_pinot, mock_kafka):
        repo = CoberturaRegionReadRepository()
        samples: list[float] = []
        for _ in range(20):
            t0 = time.perf_counter()
            repo.count_unidades_activas(1)
            samples.append((time.perf_counter() - t0) * 1000)
        samples.sort()
        p95 = samples[int(len(samples) * 0.95) - 1]
        assert p95 <= 100.0, f"p95={p95:.2f}ms exceeds 100ms"
