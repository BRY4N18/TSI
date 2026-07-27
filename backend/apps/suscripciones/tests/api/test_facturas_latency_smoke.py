"""CA-SUSF-006 smoke — historial de facturas bajo presupuesto de latencia (fixtures).

RNF-SUSF-005 (job facturación ≤ 30 min / 10k activas) queda como criterio de
aceptación manual/load post-MVP; este test solo documenta y verifica CA-SUSF-006
(historial ≤ 3 s en condiciones normales de fixtures in-memory).
"""

from __future__ import annotations

import time

import pytest

from core.repositories.suscripciones.factura_repository import FacturaRepository

pytestmark = [pytest.mark.api, pytest.mark.slow]

# CA-SUSF-006: historial ≤ 3 s en condiciones normales.
_BUDGET_SECONDS = 3.0


def test_historial_facturas_latency_smoke(api_client, proveedor_billing_auth_headers, mock_pinot, mock_kafka):
    # Arrange — varias facturas del cliente seed (idcliente=1)
    repo = FacturaRepository()
    for i in range(5):
        repo.create(
            {
                "id_cliente": 1,
                "id_suscripcion": 1,
                "periodo": f"2026-{i + 1:02d}",
                "monto_base": 20.0 + i,
            }
        )

    # Act
    started = time.perf_counter()
    response = api_client.get(
        "/api/v1/suscripciones/facturas?limit=20",
        **proveedor_billing_auth_headers,
    )
    elapsed = time.perf_counter() - started

    # Assert
    assert response.status_code == 200
    assert isinstance(response.json().get("data"), list)
    assert elapsed <= _BUDGET_SECONDS, (
        f"CA-SUSF-006: historial tardó {elapsed:.3f}s (presupuesto {_BUDGET_SECONDS}s)"
    )
