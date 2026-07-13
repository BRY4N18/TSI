import pytest


@pytest.mark.api
class TestCuentaPreferenciasContract:
    def test_get_preferencias_when_cliente_returns_envelope(self, api_client, cliente_auth_headers):
        # Act
        response = api_client.get(
            "/api/v1/cuentas-clientes/1/preferencias",
            **cliente_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["id_cliente"] == 1

    def test_patch_preferencias_when_valid_returns_updated(self, api_client, cliente_auth_headers):
        # Arrange
        payload = {
            "telefono_sms": "3001119999",
            "canales_notificacion": "sms",
        }

        # Act
        response = api_client.patch(
            "/api/v1/cuentas-clientes/1/preferencias",
            payload,
            format="json",
            **cliente_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["preferencias"]["telefono_sms"] == "3001119999"
