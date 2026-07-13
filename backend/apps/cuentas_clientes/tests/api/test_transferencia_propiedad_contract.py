import pytest


@pytest.mark.api
class TestTransferenciaPropiedadContract:
    def test_transferir_when_admin_local_returns_envelope(self, api_client, cliente_auth_headers):
        # Arrange — reset admin to 3 for test isolation
        api_client.patch(
            "/api/v1/cuentas-clientes/1/perfil",
            {"nombre": "reset"},
            format="json",
            **cliente_auth_headers,
        )
        payload = {"id_nuevo_responsable": 4}

        # Act
        response = api_client.post(
            "/api/v1/cuentas-clientes/1/transferencia-propiedad",
            payload,
            format="json",
            **cliente_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["nuevo_admin_local_id"] == 4
