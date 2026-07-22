import pytest


@pytest.mark.api
class TestRegistrarTicketContract:
    def test_registrar_when_valid_returns_201(self, api_client, cliente_auth_headers):
        # Act
        response = api_client.post(
            "/api/v1/soporte/tickets",
            {
                "idcliente": 1,
                "asunto": "La API no responde",
                "descripcion": "error 500 constante desde hace 1 hora",
                "tipo": "tecnico",
            },
            format="json",
            **cliente_auth_headers,
        )

        # Assert
        assert response.status_code == 201
        body = response.json()
        assert body["data"]["estado"] == "Abierto"
        assert body["data"]["sla_status"] == "en curso"

    def test_registrar_when_no_clasificable_returns_pendiente(self, api_client, cliente_auth_headers):
        # Act
        response = api_client.post(
            "/api/v1/soporte/tickets",
            {"idcliente": 1, "asunto": "xyz", "descripcion": "qwerty", "tipo": "otro"},
            format="json",
            **cliente_auth_headers,
        )

        # Assert
        assert response.status_code == 201
        body = response.json()
        assert body["data"]["estado"] == "Pendiente_de_clasificacion"
        assert body["data"]["sla_status"] is None

    def test_registrar_when_falta_campo_returns_400(self, api_client, cliente_auth_headers):
        # Act
        response = api_client.post(
            "/api/v1/soporte/tickets",
            {"idcliente": 1, "asunto": "Falta descripcion"},
            format="json",
            **cliente_auth_headers,
        )

        # Assert
        assert response.status_code == 400

    def test_registrar_when_unidad_returns_403(self, api_client, unidad_auth_headers):
        # Act
        response = api_client.post(
            "/api/v1/soporte/tickets",
            {"idcliente": 1, "asunto": "a", "descripcion": "b", "tipo": "tecnico"},
            format="json",
            **unidad_auth_headers,
        )

        # Assert
        assert response.status_code == 403
