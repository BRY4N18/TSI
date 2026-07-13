import pytest


@pytest.mark.api
class TestUsuariosElegiblesContract:
    def test_list_usuarios_when_admin_local_returns_list(self, api_client, cliente_auth_headers):
        # Act
        response = api_client.get(
            "/api/v1/cuentas-clientes/1/usuarios-elegibles",
            **cliente_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        usuarios = response.json()["data"]["usuarios"]
        assert len(usuarios) >= 2

    def test_list_usuarios_when_not_admin_local_returns_403(
        self, api_client, cliente_member_auth_headers
    ):
        # Act
        response = api_client.get(
            "/api/v1/cuentas-clientes/1/usuarios-elegibles",
            **cliente_member_auth_headers,
        )

        # Assert
        assert response.status_code == 403
