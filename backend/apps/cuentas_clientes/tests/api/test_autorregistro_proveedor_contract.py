import pytest


@pytest.mark.api
class TestAutorregistroProveedorContract:
    def test_autorregistro_when_valid_returns_201(self, api_client, mock_pinot, mock_kafka):
        # Arrange
        payload = {
            "razon_social": "Ambulancias Quito S.A.",
            "nombre": "Ambulancias Quito",
            "tipo": "Proveedor",
            "nit_identificacion": "820111333-2",
            "admin_local": {
                "nombres": "Maria",
                "apellidos": "Quito",
                "gmail": "maria.quito@tsi.com",
            },
        }

        # Act
        response = api_client.post(
            "/api/v1/cuentas-clientes/autorregistro",
            payload,
            format="json",
        )

        # Assert
        assert response.status_code == 201
        body = response.json()
        assert body["data"]["estado"] == "Pendiente_Aprobación"
        assert "idcliente" in body["data"]

    def test_autorregistro_when_duplicate_nit_returns_409(
        self, api_client, mock_pinot, mock_kafka
    ):
        # Arrange
        payload = {
            "razon_social": "Dup",
            "nombre": "Dup",
            "tipo": "Proveedor",
            "nit_identificacion": "900123456-1",
            "admin_local": {
                "nombres": "A",
                "apellidos": "B",
                "gmail": "dup.autor@tsi.com",
            },
        }

        # Act
        response = api_client.post(
            "/api/v1/cuentas-clientes/autorregistro",
            payload,
            format="json",
        )

        # Assert
        assert response.status_code == 409
