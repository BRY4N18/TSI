import pytest


@pytest.mark.api
class TestRegistroCuentaContract:
    def test_registrar_when_admin_returns_410_gone(self, api_client, auth_headers):
        # Arrange — CU-O01 retirado; todo cliente vía O14→O16
        payload = {
            "razon_social": "Nueva Aseguradora S.A.",
            "nombre": "Nueva Aseguradora",
            "tipo": "Aseguradora",
            "nit_identificacion": "700123456-9",
            "fecha_inicio_contrato": 1704067200000,
            "admin_local": {
                "nombres": "Pedro",
                "apellidos": "Nuevo",
                "gmail": "nuevo.admin@tsi.com",
            },
        }

        # Act
        response = api_client.post(
            "/api/v1/cuentas-clientes",
            payload,
            format="json",
            **auth_headers,
        )

        # Assert
        assert response.status_code == 410
