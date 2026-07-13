import pytest


@pytest.mark.api
class TestHistorialEstadoContract:
    def test_historial_when_admin_returns_200(
        self, api_client, admin_auth_headers, unidad_con_estado_activa
    ):
        # Act
        response = api_client.get(
            "/api/v1/unidades-emergencia/1/historial-estado",
            **admin_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) >= 1

    def test_historial_when_unidad_other_unit_returns_403(
        self, api_client, unidad_auth_headers
    ):
        # Act
        response = api_client.get(
            "/api/v1/unidades-emergencia/2/historial-estado",
            **unidad_auth_headers,
        )

        # Assert
        assert response.status_code == 403

    def test_declarar_por_admin_returns_201(
        self, api_client, admin_auth_headers, unidad_con_estado_activa
    ):
        # Act
        response = api_client.post(
            "/api/v1/unidades-emergencia/1/historial-estado",
            {"estadonuevo": "Ocupada"},
            format="json",
            **admin_auth_headers,
        )

        # Assert
        assert response.status_code == 201
        assert response.json()["data"]["estadonuevo"] == "Ocupada"
