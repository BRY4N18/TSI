import pytest


@pytest.mark.api
class TestEjecutarValidacionContract:
    URL = "/api/v1/red-operativa/regiones/validaciones"

    def test_post_when_alta_y_aprobada_returns_200_con_produccion(
        self, api_client, director_tecnologico_auth_headers
    ):
        # Act
        response = api_client.post(
            self.URL,
            {"idestado": 2, "nombreregion": "Guadalajara", "resultado": "Aprobada"},
            format="json",
            **director_tecnologico_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        body = response.json()
        assert body["data"]["estadoregion_actual"] == "Producción"

    def test_post_when_alta_y_rechazada_returns_200_con_en_validacion(
        self, api_client, director_tecnologico_auth_headers
    ):
        # Act
        response = api_client.post(
            self.URL,
            {
                "idestado": 2,
                "nombreregion": "Monterrey",
                "resultado": "Rechazada",
                "motivo": "Latencia fuera de rango",
            },
            format="json",
            **director_tecnologico_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["estadoregion_actual"] == "En_Validación"

    def test_post_when_rechazada_sin_motivo_returns_400(
        self, api_client, director_tecnologico_auth_headers
    ):
        # Act
        response = api_client.post(
            self.URL,
            {"idestado": 2, "nombreregion": "Monterrey", "resultado": "Rechazada"},
            format="json",
            **director_tecnologico_auth_headers,
        )

        # Assert
        assert response.status_code == 400

    def test_post_when_reingreso_desde_despublicada_returns_produccion(
        self, api_client, director_tecnologico_auth_headers, pinot_store
    ):
        # Arrange
        pinot_store["Dim_RegionOperativa"][0]["estadoregion"] = "Despublicada"

        # Act
        response = api_client.post(
            self.URL,
            {"idregionoperativa": 1, "resultado": "Aprobada"},
            format="json",
            **director_tecnologico_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["estadoregion_actual"] == "Producción"

    def test_post_when_unauthenticated_returns_403(self, api_client):
        # Act
        response = api_client.post(
            self.URL,
            {"idregionoperativa": 1, "resultado": "Aprobada"},
            format="json",
        )

        # Assert
        assert response.status_code == 403

    def test_post_when_operador_returns_403(self, api_client, operador_auth_headers):
        # Act
        response = api_client.post(
            self.URL,
            {"idregionoperativa": 1, "resultado": "Aprobada"},
            format="json",
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 403

    def test_post_when_administrador_returns_200(self, api_client, admin_auth_headers):
        # Act
        response = api_client.post(
            self.URL,
            {"idregionoperativa": 1, "resultado": "Rechazada", "motivo": "Falta info"},
            format="json",
            **admin_auth_headers,
        )

        # Assert
        assert response.status_code == 200
