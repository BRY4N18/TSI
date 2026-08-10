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

    def test_declarar_por_admin_returns_403(
        self, api_client, admin_auth_headers, unidad_con_estado_activa
    ):
        # Arrange — SRS 3.5.1/3.6.3: ningún tercero declara disponibilidad en
        # nombre de una unidad, ni siquiera un Administrador.
        # Act
        response = api_client.post(
            "/api/v1/unidades-emergencia/1/historial-estado",
            {"estadonuevo": "Ocupada"},
            format="json",
            **admin_auth_headers,
        )

        # Assert
        assert response.status_code == 403

    def test_declarar_por_propia_unidad_returns_201(
        self, api_client, unidad_auth_headers, unidad_con_estado_activa
    ):
        # Act
        response = api_client.post(
            "/api/v1/unidades-emergencia/1/historial-estado",
            {"estadonuevo": "Fuera de servicio"},
            format="json",
            **unidad_auth_headers,
        )

        # Assert
        assert response.status_code == 201
        assert response.json()["data"]["estadonuevo"] == "Fuera de servicio"

    def test_declarar_por_otra_unidad_returns_403(
        self, api_client, unidad_auth_headers, unidad_con_estado_activa
    ):
        # Arrange — unidad_auth_headers está ligada a idunidademergencia=1;
        # intenta declarar disponibilidad de otra unidad (2).
        # Act
        response = api_client.post(
            "/api/v1/unidades-emergencia/2/historial-estado",
            {"estadonuevo": "Activa"},
            format="json",
            **unidad_auth_headers,
        )

        # Assert
        assert response.status_code == 403
