import pytest

from apps.accidentes.domain_constants import ESTADO_BORRADOR, ESTADO_DESCARTADO


@pytest.mark.api
class TestDescartarCasoContract:
    def test_descartar_when_borrador_returns_200(
        self, api_client, operador_auth_headers, seed_accidente
    ):
        # Arrange
        aid = seed_accidente(idaccidente="ACC-DESC-1", estado=ESTADO_BORRADOR)

        # Act
        response = api_client.post(
            f"/api/v1/accidentes/{aid}/descartar",
            {"motivo": "falsa alarma"},
            format="json",
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["data"]["estado"] == ESTADO_DESCARTADO

    def test_descartar_when_reportado_returns_409(
        self, api_client, operador_auth_headers, seed_accidente
    ):
        # Arrange
        aid = seed_accidente(idaccidente="ACC-DESC-2", estado="REPORTADO")

        # Act
        response = api_client.post(
            f"/api/v1/accidentes/{aid}/descartar",
            {},
            format="json",
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 409
