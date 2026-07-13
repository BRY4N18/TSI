import pytest


@pytest.mark.api
class TestListarPendientesContract:
    def test_listar_when_unidad_with_pendiente_returns_200(
        self,
        api_client,
        unidad_auth_headers,
        accidente_activo,
        unidad_con_estado_activa,
        despacho_pendiente_unidad,
    ):
        # Act
        response = api_client.get(
            "/api/v1/mi-despacho/pendientes",
            **unidad_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert len(body["data"]["pendientes"]) >= 1

    def test_listar_when_tecnico_returns_403(self, api_client, tecnico_auth_headers):
        # Act
        response = api_client.get(
            "/api/v1/mi-despacho/pendientes",
            **tecnico_auth_headers,
        )

        # Assert
        assert response.status_code == 403
