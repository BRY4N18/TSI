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


@pytest.mark.api
class TestPartnerPuedeDisputar:
    """F18 — el SRS dice que el partner puede registrar una disputa sobre su
    factura. `PartnerIntegracion` recibia 403 y la disputa quedaba sin nadie que
    pudiera abrirla desde su lado."""

    def test_partner_integracion_puede_registrar_una_disputa(
        self, api_client, partner_auth_headers
    ):
        # Act
        response = api_client.post(
            "/api/v1/soporte/tickets",
            {
                "idcliente": 1,
                "asunto": "Cargo de excedente no reconocido",
                "descripcion": "El detalle de llamadas no cuadra con el monto facturado",
                "tipo": "tecnico",
            },
            format="json",
            **partner_auth_headers,
        )

        # Assert
        assert response.status_code == 201

    def test_partner_integracion_ve_el_ticket_que_abrio(
        self, api_client, partner_auth_headers
    ):
        # Arrange — abrirlo y no poder seguirlo seria la misma puerta cerrada un
        # paso mas adelante.
        creado = api_client.post(
            "/api/v1/soporte/tickets",
            {
                "idcliente": 1,
                "asunto": "Cargo de excedente no reconocido",
                "descripcion": "El detalle de llamadas no cuadra con el monto",
                "tipo": "tecnico",
            },
            format="json",
            **partner_auth_headers,
        )
        assert creado.status_code == 201, creado.content
        creado = creado.json()["data"]

        # Act
        response = api_client.get(
            f"/api/v1/soporte/tickets/{creado['id_reclamo']}", **partner_auth_headers
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["ticket"]["id_reclamo"] == creado["id_reclamo"]

    def test_un_rol_sin_relacion_con_soporte_sigue_recibiendo_403(
        self, api_client, unidad_auth_headers
    ):
        # Act — abrir el permiso al partner no puede abrirlo a cualquiera
        response = api_client.post(
            "/api/v1/soporte/tickets",
            {
                "idcliente": 1,
                "asunto": "No deberia poder",
                "descripcion": "Una unidad de campo no reporta tickets de cliente",
                "tipo": "tecnico",
            },
            format="json",
            **unidad_auth_headers,
        )

        # Assert
        assert response.status_code == 403

    def test_partner_ajeno_no_ve_el_ticket_de_otro_cliente(
        self, api_client, partner_auth_headers, partner_ajeno_auth_headers
    ):
        """El acotamiento se decidia con `roles == {'Cliente'}`: admitir al
        partner sin tocarlo lo habria dejado FUERA del filtro, viendo tickets
        ajenos y notas internas."""
        # Arrange
        creado = api_client.post(
            "/api/v1/soporte/tickets",
            {
                "idcliente": 1,
                "asunto": "Cargo de excedente no reconocido",
                "descripcion": "El detalle de llamadas no cuadra con el monto",
                "tipo": "tecnico",
            },
            format="json",
            **partner_auth_headers,
        ).json()["data"]

        # Act
        response = api_client.get(
            f"/api/v1/soporte/tickets/{creado['id_reclamo']}", **partner_ajeno_auth_headers
        )

        # Assert
        assert response.status_code == 403
