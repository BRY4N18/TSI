import pytest

from apps.cuentas_clientes.services.autorregistro_proveedor_service import (
    AutorregistroProveedorService,
)


@pytest.mark.slow
@pytest.mark.service
class TestAutorregistroProveedorP95:
    def test_autorregistrar_p95_under_threshold(self, mock_pinot, mock_kafka):
        # Arrange — CU-O14 (reemplaza p95 de O01 retirado)
        service = AutorregistroProveedorService()
        samples_ms: list[float] = []

        # Act
        for i in range(20):
            import time

            payload = {
                "razon_social": f"Perf Test {i} S.A.",
                "nombre": f"Perf{i}",
                "tipo": "Proveedor",
                "nit_identificacion": f"900999{i:03d}-7",
                "admin_local": {
                    "nombres": "Perf",
                    "apellidos": "User",
                    "gmail": f"perf{i}@tsi.com",
                },
            }
            start = time.perf_counter()
            service.autorregistrar(data=payload)
            samples_ms.append((time.perf_counter() - start) * 1000)

        samples_ms.sort()
        p95 = samples_ms[int(len(samples_ms) * 0.95) - 1]

        # Assert
        assert p95 <= 800
