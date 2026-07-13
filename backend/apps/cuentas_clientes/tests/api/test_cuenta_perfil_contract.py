import pytest


@pytest.mark.api
class TestCuentaPerfilContract:
    def test_get_perfil_when_cliente_returns_envelope(self, api_client, cliente_auth_headers):
        # Act
        response = api_client.get("/api/v1/cuentas-clientes/1/perfil", **cliente_auth_headers)

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert body["data"]["idcliente"] == 1
        assert body["data"]["razon_social"] == "Empresa Demo S.A.S."

    def test_patch_perfil_when_cliente_updates_returns_campos(self, api_client, cliente_auth_headers):
        # Arrange
        payload = {"nombre": "Empresa Renombrada"}

        # Act
        response = api_client.patch(
            "/api/v1/cuentas-clientes/1/perfil",
            payload,
            format="json",
            **cliente_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert "campos_modificados" in body["data"]
        assert body["data"]["perfil"]["nombre"] == "Empresa Renombrada"

    def test_get_perfil_when_unauthenticated_returns_401(self, api_client):
        # Act
        response = api_client.get("/api/v1/cuentas-clientes/1/perfil")

        # Assert
        assert response.status_code == 401
