"""SC-007 / testing.md — list unidades filtrado ≤100ms p95 (mock Pinot)."""

from __future__ import annotations

import time

import pytest

from core.repositories.red_operativa.unidad_emergencia_repository import (
    UnidadEmergenciaRepository,
)


@pytest.mark.slow
class TestListUnidadesP95:
    def test_list_by_cliente_p95_under_100ms(
        self, mock_pinot, mock_kafka, pinot_store, mock_unidad_emergencia
    ):
        base = dict(mock_unidad_emergencia)
        for i in range(50):
            pinot_store["Dim_UnidadEmergencia"].append(
                {
                    **base,
                    "idunidademergencia": 8000 + i,
                    "placa": f"PERF-{i:03d}",
                    "unidademergencia": f"Unidad perf {i}",
                }
            )

        repo = UnidadEmergenciaRepository()
        idcliente = int(base["idcliente"])
        samples: list[float] = []
        for _ in range(20):
            t0 = time.perf_counter()
            repo.list_by_cliente(idcliente, cursor=0, limit=20, q="PERF")
            samples.append((time.perf_counter() - t0) * 1000)
        samples.sort()
        p95 = samples[int(len(samples) * 0.95) - 1]
        assert p95 <= 100.0, f"p95={p95:.2f}ms exceeds 100ms"
