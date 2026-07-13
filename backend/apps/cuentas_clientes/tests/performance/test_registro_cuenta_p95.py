import pytest

from apps.cuentas_clientes.services.registro_cuenta_service import RegistroCuentaService


@pytest.mark.slow
@pytest.mark.service
class TestRegistroCuentaP95:
    def test_registrar_p95_under_threshold(self, mock_pinot, mock_kafka):
        # Arrange
        service = RegistroCuentaService()
        data = {
            "razon_social": "Perf Test S.A.",
            "nombre": "Perf",
            "tipo": "Aseguradora",
            "nit_identificacion": "900999888-7",
            "fecha_inicio_contrato": 1704067200000,
            "admin_local": {
                "nombres": "Perf",
                "apellidos": "User",
                "gmail": "perf.user@tsi.com",
            },
        }
        samples_ms: list[float] = []

        # Act
        for i in range(20):
            import time

            payload = {**data, "nit_identificacion": f"900999{i:03d}-7",
                       "admin_local": {**data["admin_local"], "gmail": f"perf{i}@tsi.com"}}
            start = time.perf_counter()
            service.registrar(user_id=1, roles=["Administrador"], data=payload)
            samples_ms.append((time.perf_counter() - start) * 1000)

        samples_ms.sort()
        p95 = samples_ms[int(len(samples_ms) * 0.95) - 1]

        # Assert
        assert p95 <= 300
