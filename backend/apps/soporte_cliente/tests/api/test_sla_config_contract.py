import pytest


@pytest.mark.api
class TestSLAConfigContract:
    def test_get_when_admin_returns_200(self, api_client, auth_headers):
        # Act
        response = api_client.get("/api/v1/soporte/sla-config", **auth_headers)

        # Assert
        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) >= 2

    def test_post_when_admin_returns_201(self, api_client, auth_headers):
        # Act
        response = api_client.post(
            "/api/v1/soporte/sla-config",
            {
                "idplan": 1,
                "tipoincidencia": "consulta_general",
                "prioridad": "baja",
                "tiemporespuestamax": 3600,
                "tiemporesolucionmax": 86400,
            },
            format="json",
            **auth_headers,
        )

        # Assert
        assert response.status_code == 201
        assert response.json()["data"]["activo"] is True

    def test_post_when_agente_returns_403(self, api_client, agente_soporte_auth_headers):
        # Act
        response = api_client.post(
            "/api/v1/soporte/sla-config",
            {
                "idplan": 1,
                "tipoincidencia": "x",
                "prioridad": "baja",
                "tiemporespuestamax": 3600,
                "tiemporesolucionmax": 86400,
            },
            format="json",
            **agente_soporte_auth_headers,
        )

        # Assert
        assert response.status_code == 403

    def test_post_when_campos_faltantes_returns_400(self, api_client, auth_headers):
        # Act
        response = api_client.post(
            "/api/v1/soporte/sla-config", {"idplan": 1}, format="json", **auth_headers
        )

        # Assert
        assert response.status_code == 400
