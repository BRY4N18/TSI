import pytest


@pytest.mark.api
class TestReenviarInvitacionContract:
    def test_reenviar_when_admin_returns_200(self, api_client, auth_headers):
        # Act
        response = api_client.post(
            "/api/v1/cuentas-clientes/1/invitacion/reenviar",
            {},
            format="json",
            **auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["message"] == "Invitación reenviada"
        assert body["data"]["id_usuario"] == 3

    def test_reenviar_when_not_member_returns_403(
        self, api_client, cliente_member_auth_headers
    ):
        # Act
        response = api_client.post(
            "/api/v1/cuentas-clientes/1/invitacion/reenviar",
            {},
            format="json",
            **cliente_member_auth_headers,
        )

        # Assert
        assert response.status_code == 403
