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

    def test_registrar_when_idservicio_persists(self, api_client, cliente_auth_headers):
        response = api_client.post(
            "/api/v1/soporte/tickets",
            {
                "idcliente": 1,
                "asunto": "API timeout",
                "descripcion": "error 500 en endpoint de despacho",
                "tipo": "tecnico",
                "idservicio": 3,
            },
            format="json",
            **cliente_auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["data"]["idservicio"] == 3

    def test_registrar_when_idfactura_persists(self, api_client, cliente_auth_headers):
        # RF-O83.2 — vincular una factura en disputa (opcional)
        response = api_client.post(
            "/api/v1/soporte/tickets",
            {
                "idcliente": 1,
                "asunto": "Cobro duplicado",
                "descripcion": "la factura fue cobrada dos veces",
                "tipo": "administrativo",
                "idfactura": "3f2b8c14-5d6e-4a7b-9c0d-1e2f3a4b5c6d",
            },
            format="json",
            **cliente_auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["data"]["idfactura"] == "3f2b8c14-5d6e-4a7b-9c0d-1e2f3a4b5c6d"

    def test_registrar_when_idfactura_ya_tiene_disputa_abierta_returns_422(
        self, api_client, cliente_auth_headers
    ):
        # RF-O83.2 — una factura admite una sola disputa (ticket) abierta a la vez
        primero = api_client.post(
            "/api/v1/soporte/tickets",
            {
                "idcliente": 1,
                "asunto": "Cobro duplicado",
                "descripcion": "la factura fue cobrada dos veces",
                "tipo": "administrativo",
                "idfactura": "3f2b8c14-5d6e-4a7b-9c0d-1e2f3a4b5c6d",
            },
            format="json",
            **cliente_auth_headers,
        )
        assert primero.status_code == 201

        segundo = api_client.post(
            "/api/v1/soporte/tickets",
            {
                "idcliente": 1,
                "asunto": "Otra disputa sobre la misma factura",
                "descripcion": "sigo sin estar de acuerdo con el cobro",
                "tipo": "administrativo",
                "idfactura": "3f2b8c14-5d6e-4a7b-9c0d-1e2f3a4b5c6d",
            },
            format="json",
            **cliente_auth_headers,
        )
        assert segundo.status_code == 422
