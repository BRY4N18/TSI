import pytest


@pytest.mark.api
class TestListUnidadesContract:
    def test_get_unidades_when_proveedor_returns_200(
        self, api_client, proveedor_auth_headers, mock_unidad_emergencia
    ):
        response = api_client.get(
            "/api/v1/red-operativa/unidades",
            **proveedor_auth_headers,
        )

        assert response.status_code == 200
        body = response.json()
        items = body["data"]["items"]
        assert isinstance(items, list)
        assert any(
            u["idunidademergencia"] == mock_unidad_emergencia["idunidademergencia"] for u in items
        )
        pagination = body["meta"]["pagination"]
        assert "next_cursor" in pagination
        assert pagination["limit"] == 20

    def test_get_unidades_respects_limit_and_next_cursor(
        self, api_client, proveedor_auth_headers, pinot_store, mock_unidad_emergencia
    ):
        base = dict(mock_unidad_emergencia)
        for i in range(3):
            row = {
                **base,
                "idunidademergencia": 9000 + i,
                "placa": f"PAG-{i}",
                "unidademergencia": f"Unidad pag {i}",
            }
            pinot_store["Dim_UnidadEmergencia"].append(row)

        response = api_client.get(
            "/api/v1/red-operativa/unidades?limit=2",
            **proveedor_auth_headers,
        )
        assert response.status_code == 200
        body = response.json()
        items = body["data"]["items"]
        assert len(items) <= 2
        next_cursor = body["meta"]["pagination"]["next_cursor"]
        assert body["meta"]["pagination"]["limit"] == 2

        if next_cursor is not None:
            page2 = api_client.get(
                f"/api/v1/red-operativa/unidades?limit=2&cursor={next_cursor}",
                **proveedor_auth_headers,
            )
            assert page2.status_code == 200
            ids_page1 = {u["idunidademergencia"] for u in items}
            ids_page2 = {u["idunidademergencia"] for u in page2.json()["data"]["items"]}
            assert ids_page1.isdisjoint(ids_page2)
            assert all(uid > next_cursor for uid in ids_page2)

    def test_get_unidades_filters_q_activo_tipo(
        self, api_client, proveedor_auth_headers, pinot_store, mock_unidad_emergencia
    ):
        base = dict(mock_unidad_emergencia)
        pinot_store["Dim_UnidadEmergencia"].append(
            {
                **base,
                "idunidademergencia": 9101,
                "placa": "FILT-AAA",
                "unidademergencia": "Ambulancia Filtro",
                "tipounidademergencia": "Ambulancia",
                "activo": True,
            }
        )
        pinot_store["Dim_UnidadEmergencia"].append(
            {
                **base,
                "idunidademergencia": 9102,
                "placa": "FILT-BBB",
                "unidademergencia": "Grua Baja",
                "tipounidademergencia": "Grúa",
                "activo": False,
            }
        )

        by_q = api_client.get(
            "/api/v1/red-operativa/unidades?q=FILT-AAA",
            **proveedor_auth_headers,
        )
        assert by_q.status_code == 200
        placas = [u["placa"] for u in by_q.json()["data"]["items"]]
        assert placas == ["FILT-AAA"]

        by_activo = api_client.get(
            "/api/v1/red-operativa/unidades?activo=false&q=FILT",
            **proveedor_auth_headers,
        )
        assert by_activo.status_code == 200
        items_baja = by_activo.json()["data"]["items"]
        assert len(items_baja) == 1
        assert items_baja[0]["placa"] == "FILT-BBB"
        assert items_baja[0]["activo"] is False

        by_tipo = api_client.get(
            "/api/v1/red-operativa/unidades?tipounidademergencia=Ambulancia&q=FILT",
            **proveedor_auth_headers,
        )
        assert by_tipo.status_code == 200
        assert all(u["tipounidademergencia"] == "Ambulancia" for u in by_tipo.json()["data"]["items"])

    def test_get_unidades_when_operador_returns_403(self, api_client, operador_auth_headers):
        response = api_client.get(
            "/api/v1/red-operativa/unidades",
            **operador_auth_headers,
        )
        assert response.status_code == 403

    def test_get_unidades_when_unauthenticated_returns_401(self, api_client):
        response = api_client.get("/api/v1/red-operativa/unidades")
        assert response.status_code == 401
