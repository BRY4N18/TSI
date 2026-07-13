import pytest

from apps.accidentes.domain_constants import ESTADO_FUSIONADO


@pytest.mark.api
class TestFusionarReportesContract:
    def test_fusionar_when_valid_returns_200(
        self, api_client, operador_auth_headers, seed_accidente
    ):
        # Arrange
        principal = seed_accidente(idaccidente="ACC-PARENT")
        duplicado = seed_accidente(idaccidente="ACC-DUP-F")

        # Act
        response = api_client.post(
            f"/api/v1/accidentes/{duplicado}/fusionar",
            {"idaccidenteprincipal": principal, "confirmacion": True},
            format="json",
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["estado_duplicado"] == ESTADO_FUSIONADO
