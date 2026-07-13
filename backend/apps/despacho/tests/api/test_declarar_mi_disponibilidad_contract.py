import pytest


@pytest.mark.api
class TestDeclararMiDisponibilidadContract:
    def test_declarar_when_unidad_returns_201(
        self, api_client, unidad_auth_headers, unidad_con_estado_activa
    ):
        # Act
        response = api_client.post(
            "/api/v1/mi-unidad-emergencia/disponibilidad",
            {"estadonuevo": "Ocupada"},
            format="json",
            **unidad_auth_headers,
        )

        # Assert
        assert response.status_code == 201
        body = response.json()
        assert body["data"]["estadoanterior"] == "Activa"
        assert body["data"]["estadonuevo"] == "Ocupada"

    def test_declarar_when_tecnico_returns_403(
        self, api_client, tecnico_auth_headers
    ):
        # Act
        response = api_client.post(
            "/api/v1/mi-unidad-emergencia/disponibilidad",
            {"estadonuevo": "Activa"},
            format="json",
            **tecnico_auth_headers,
        )

        # Assert
        assert response.status_code == 403
