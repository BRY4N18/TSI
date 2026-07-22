import pytest


@pytest.mark.api
class TestRegistrarAccidenteContract:
    def test_registrar_when_valid_returns_201_reportado(
        self, api_client, operador_auth_headers, accidente_payload
    ):
        # Act
        response = api_client.post(
            "/api/v1/accidentes",
            accidente_payload,
            format="json",
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 201
        body = response.json()
        assert body["data"]["estado"] == "REPORTADO"
        assert "idaccidente" in body["data"]

    def test_registrar_when_unauthenticated_returns_401(self, api_client, accidente_payload):
        # Act
        response = api_client.post("/api/v1/accidentes", accidente_payload, format="json")

        # Assert
        assert response.status_code in (401, 403)

    def test_registrar_when_duplicate_without_forzar_returns_409(
        self, api_client, operador_auth_headers, accidente_payload, mock_pinot, mock_kafka
    ):
        # Arrange
        from core.repositories.accidentes.accidente_repository import (
            AccidenteRepository,
        )

        ts = accidente_payload["fechahoraaccidente"]
        AccidenteRepository().create(
            {
                "idaccidente": "ACC-DUP",
                "latitudinicio": accidente_payload["latitudinicio"],
                "longitudinicio": accidente_payload["longitudinicio"],
                "fechahoraaccidente": ts,
                "activo": True,
            }
        )

        # Act
        response = api_client.post(
            "/api/v1/accidentes",
            accidente_payload,
            format="json",
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 409
        assert response.json()["data"]["error"] == "duplicado_posible"

    def test_registrar_when_gps_out_of_range_returns_400(
        self, api_client, operador_auth_headers, accidente_payload
    ):
        # Arrange
        payload = {**accidente_payload, "latitudinicio": 200.0}

        # Act
        response = api_client.post(
            "/api/v1/accidentes",
            payload,
            format="json",
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["code"] == "400"

    def test_registrar_when_missing_required_field_returns_400(
        self, api_client, operador_auth_headers, accidente_payload
    ):
        # Arrange
        payload = {k: v for k, v in accidente_payload.items() if k != "descripcion"}

        # Act
        response = api_client.post(
            "/api/v1/accidentes",
            payload,
            format="json",
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["code"] == "400"
