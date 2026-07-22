import pytest

from core.repositories.accidentes.estado_accidente_repository import (
    EstadoAccidenteRepository,
)


@pytest.mark.api
class TestConfirmarReporteContract:
    def test_confirmar_when_borrador_returns_200(
        self, api_client, operador_auth_headers, accidente_payload
    ):
        # Arrange — fuera de cobertura fuerza BORRADOR aun con forzarAdvertencias
        payload = {**accidente_payload, "idcalle": 99}
        create_resp = api_client.post(
            "/api/v1/accidentes?forzarAdvertencias=true",
            payload,
            format="json",
            **operador_auth_headers,
        )
        assert create_resp.status_code == 201
        assert create_resp.json()["data"]["estado"] == "BORRADOR"
        idaccidente = create_resp.json()["data"]["idaccidente"]

        # Act
        response = api_client.post(
            f"/api/v1/accidentes/{idaccidente}/confirmar-reporte",
            {"confirmacion": True},
            format="json",
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["estado"] == "REPORTADO"

    def test_confirmar_when_not_borrador_returns_409(
        self, api_client, operador_auth_headers, accidente_payload
    ):
        # Arrange
        create_resp = api_client.post(
            "/api/v1/accidentes",
            accidente_payload,
            format="json",
            **operador_auth_headers,
        )
        idaccidente = create_resp.json()["data"]["idaccidente"]

        # Act
        response = api_client.post(
            f"/api/v1/accidentes/{idaccidente}/confirmar-reporte",
            {"confirmacion": True},
            format="json",
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 409
