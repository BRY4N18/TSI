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

    def test_descartar_when_reportado_sin_despacho_returns_200(
        self, api_client, operador_auth_headers, seed_accidente
    ):
        """SRS §3.6.1: el gate es "no existe despacho", no "está en BORRADOR".

        Antes esto devolvía 409 y, como el registro se autoconfirma a REPORTADO
        cuando no hay advertencias, dejaba las falsas alarmas limpias sin forma de
        descartarse.
        """
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
        assert response.status_code == 200
        assert response.json()["data"]["estado"] == "DESCARTADO"

    def test_descartar_when_cerrado_returns_409(
        self, api_client, operador_auth_headers, seed_accidente
    ):
        # Arrange
        aid = seed_accidente(idaccidente="ACC-DESC-3", estado="CERRADO")

        # Act
        response = api_client.post(
            f"/api/v1/accidentes/{aid}/descartar",
            {},
            format="json",
            **operador_auth_headers,
        )

        # Assert
        assert response.status_code == 409
